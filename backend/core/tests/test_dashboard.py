from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Usuario


@pytest.mark.django_db
def test_dashboard_metricas_autenticado():
    usuario = Usuario.objects.create_user(
        email="teste_dashboard@uea.edu.br",
        nome_completo="Usuario Teste Dashboard",
        tipo_usuario="ADMINISTRADOR",
    )
    client = APIClient()
    client.force_authenticate(user=usuario)

    url = reverse("dashboard-metricas")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "em_desenvolvimento" in response.data
    assert "apresentados" in response.data
    assert "nao_apresentados" in response.data
    assert "aprovados_publicacao" in response.data
    assert "orientacoes_por_docente" in response.data
    assert "bancas_por_docente" in response.data


@pytest.mark.django_db
def test_ct_dsh_01_numeros_batem_com_consulta_direta(
    criar_aluno, orientador, outros_docentes, area
):
    """CT-DSH-01 (C13): os indicadores batem com a contagem direta no banco.

    TCC inativado (soft delete) nao conta em nenhum indicador (RD17).
    """
    from django.utils import timezone

    from core.models import TCC, ParticipacaoBanca
    from core.services import banca as servico_banca
    from core.services import tcc as servico_tcc

    def novo_tcc(status="EM_DESENVOLVIMENTO", ativo=True):
        tcc = servico_tcc.cadastrar_tcc(
            dados={
                "titulo": "TCC do dashboard",
                "area_conhecimento": area,
                "modalidade": "DEFESA_EM_BANCA",
                "autor": criar_aluno(),
                "orientador": orientador,
            },
            usuario=orientador.usuario,
        )
        extras = {}
        if status == "NAO_APRESENTADO":
            extras["motivo_nao_apresentacao"] = "DESISTENCIA"
        if not ativo:
            extras["motivo_inativacao"] = "Cadastro duplicado"
        TCC.objects.filter(pk=tcc.pk).update(status=status, ativo=ativo, **extras)
        return tcc

    for _ in range(3):
        novo_tcc()
    novo_tcc(status="APRESENTADO")
    novo_tcc(status="NAO_APRESENTADO")
    novo_tcc(status="APROVADO_POR_PUBLICACAO")
    novo_tcc(ativo=False)  # inativado: fica fora de tudo
    com_banca = novo_tcc()
    servico_banca.cadastrar_banca(
        tcc=com_banca,
        titulares=[
            orientador.usuario,
            outros_docentes[0].usuario,
            outros_docentes[1].usuario,
        ],
        data_hora_inicio=timezone.now() + timedelta(days=7),
        tipo_local="PRESENCIAL",
        bloco="NUCOMP",
        sala="10",
        usuario=orientador.usuario,
    )

    usuario = Usuario.objects.create_user(
        email="admin_dsh01@uea.edu.br",
        nome_completo="Admin DSH-01",
        tipo_usuario="ADMINISTRADOR",
    )
    client = APIClient()
    client.force_authenticate(user=usuario)
    dados = client.get(reverse("dashboard-metricas")).data

    ativos = TCC.objects.filter(ativo=True)
    assert (
        dados["em_desenvolvimento"]
        == ativos.filter(status="EM_DESENVOLVIMENTO").count()
        == 4
    )
    assert dados["apresentados"] == 1
    assert dados["nao_apresentados"] == 1
    assert dados["aprovados_publicacao"] == 1

    orientacoes = {
        d["id"]: d["qtd_orientacoes"] for d in dados["orientacoes_por_docente"]
    }
    assert orientacoes[str(orientador.usuario_id)] == 4

    bancas = {d["id"]: d["qtd_bancas"] for d in dados["bancas_por_docente"]}
    for docente in (orientador, outros_docentes[0], outros_docentes[1]):
        esperado = ParticipacaoBanca.objects.filter(usuario=docente.usuario).count()
        assert bancas[str(docente.usuario_id)] == esperado == 1
    assert bancas[str(outros_docentes[2].usuario_id)] == 0


@pytest.mark.parametrize(
    ("tipo_usuario", "esperado"),
    [
        ("ADMINISTRADOR", status.HTTP_200_OK),
        ("DOCENTE", status.HTTP_200_OK),
        ("SECRETARIA", status.HTTP_200_OK),
        ("ALUNO", status.HTTP_403_FORBIDDEN),
        ("MEMBRO_EXTERNO", status.HTTP_403_FORBIDDEN),
    ],
)
def test_dashboard_metricas_so_para_perfis_de_gestao(tipo_usuario, esperado):
    """Aluno e membro externo nao veem os indicadores nem a carga dos docentes."""
    usuario = Usuario.objects.create_user(
        email=f"dash_{tipo_usuario.lower()}@uea.edu.br",
        nome_completo=f"Usuario {tipo_usuario}",
        tipo_usuario=tipo_usuario,
    )
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get(reverse("dashboard-metricas"))

    assert response.status_code == esperado


@pytest.mark.django_db
def test_dashboard_metricas_exige_login():
    response = APIClient().get(reverse("dashboard-metricas"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
