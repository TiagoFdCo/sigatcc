"""Testes do B8 (cadastro de banca)."""

from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import TCC, Banca, Convite, LogAuditoria, ParticipacaoBanca
from core.services import banca as servico

pytestmark = pytest.mark.django_db

URL = "/api/bancas/"


def _cadastrar(dados, usuario, **troca):
    return servico.cadastrar_banca(**{**dados, **troca}, usuario=usuario)


def test_banca_valida_grava_participacoes_convites_e_log(dados_banca, orientador):
    banca = _cadastrar(dados_banca, orientador.usuario)

    titulares = ParticipacaoBanca.objects.filter(banca=banca, tipo_membro="TITULAR")
    assert titulares.count() == 3
    assert (
        ParticipacaoBanca.objects.filter(banca=banca, tipo_membro="SUPLENTE").count()
        == 1
    )
    convites = Convite.objects.filter(banca=banca)
    assert convites.count() == 3  # 2 titulares + 1 suplente; o orientador nao recebe
    assert not convites.filter(usuario=orientador.usuario).exists()
    assert set(convites.values_list("status", flat=True)) == {"PENDENTE"}
    assert set(convites.values_list("tipo", flat=True)) == {"BANCA"}
    assert LogAuditoria.objects.filter(entidade="BANCA", registro_id=banca.id).exists()


def test_suplentes_sao_opcionais(dados_banca, orientador):
    dados = {k: v for k, v in dados_banca.items() if k != "suplentes"}
    banca = servico.cadastrar_banca(**dados, usuario=orientador.usuario)
    assert banca.participacoes.count() == 3


@pytest.mark.parametrize("qtd", [2, 4])
def test_numero_errado_de_titulares_e_recusado(
    dados_banca, orientador, outros_docentes, qtd
):
    pessoas = [orientador.usuario, *(d.usuario for d in outros_docentes)]
    with pytest.raises(ValidationError, match="exatamente 3"):
        _cadastrar(
            dados_banca, orientador.usuario, titulares=pessoas[:qtd], suplentes=[]
        )


def test_titular_repetido_e_recusado(dados_banca, orientador, outros_docentes):
    repetido = outros_docentes[0].usuario
    with pytest.raises(ValidationError, match="exatamente 3"):
        _cadastrar(
            dados_banca,
            orientador.usuario,
            titulares=[orientador.usuario, repetido, repetido],
        )


def test_banca_sem_o_orientador_e_recusada(dados_banca, orientador, outros_docentes):
    with pytest.raises(ValidationError, match="orientador deve ser"):
        _cadastrar(
            dados_banca,
            orientador.usuario,
            titulares=[d.usuario for d in outros_docentes[:3]],
            suplentes=[],
        )


def test_membro_titular_e_suplente_e_recusado(dados_banca, orientador, outros_docentes):
    with pytest.raises(ValidationError, match="titular e suplente"):
        _cadastrar(
            dados_banca, orientador.usuario, suplentes=[outros_docentes[0].usuario]
        )


def test_suplente_repetido_e_recusado(dados_banca, orientador, outros_docentes):
    s = outros_docentes[2].usuario
    with pytest.raises(ValidationError, match="suplente repetido"):
        _cadastrar(dados_banca, orientador.usuario, suplentes=[s, s])


def test_aluno_nao_compoe_banca(dados_banca, orientador, criar_aluno):
    with pytest.raises(ValidationError, match="não pode compor banca"):
        _cadastrar(dados_banca, orientador.usuario, suplentes=[criar_aluno().usuario])


def test_docente_inativo_nao_compoe_banca(dados_banca, orientador, criar_docente):
    inativo = criar_docente(ativo=False).usuario
    with pytest.raises(ValidationError, match="não pode compor banca"):
        _cadastrar(dados_banca, orientador.usuario, suplentes=[inativo])


def test_membro_externo_pode_ser_titular(dados_banca, orientador, membro_externo):
    titulares = [*dados_banca["titulares"][:2], membro_externo.usuario]
    banca = _cadastrar(dados_banca, orientador.usuario, titulares=titulares)
    assert banca.participacoes.filter(usuario=membro_externo.usuario).exists()


@pytest.mark.parametrize("delta", [timedelta(0), timedelta(days=-1)])
def test_data_que_nao_e_futura_e_recusada(dados_banca, orientador, delta):
    with pytest.raises(ValidationError, match="futura"):
        _cadastrar(
            dados_banca, orientador.usuario, data_hora_inicio=timezone.now() + delta
        )


@pytest.mark.parametrize("campo", ["bloco", "sala"])
@pytest.mark.parametrize("valor", ["", "   ", None])
def test_presencial_exige_bloco_e_sala(dados_banca, orientador, campo, valor):
    with pytest.raises(ValidationError) as erro:
        _cadastrar(dados_banca, orientador.usuario, **{campo: valor})
    assert campo in erro.value.detail


def test_presencial_guarda_bloco_e_sala_sem_link(dados_banca, orientador):
    banca = _cadastrar(
        dados_banca,
        orientador.usuario,
        bloco="  NUCOMP ",
        sala=" 10 ",
        link_remoto="https://meet.exemplo.com/abc",
    )
    assert (banca.bloco, banca.sala, banca.link_remoto) == ("NUCOMP", "10", None)


@pytest.mark.parametrize("link", [None, "", "Sala 10", "ftp://exemplo.com/x"])
def test_banca_remota_exige_link_valido(dados_banca, orientador, link):
    with pytest.raises(ValidationError, match="link válido"):
        _cadastrar(
            dados_banca, orientador.usuario, tipo_local="REMOTO", link_remoto=link
        )


def test_banca_remota_guarda_so_o_link(dados_banca, orientador):
    banca = _cadastrar(
        dados_banca,
        orientador.usuario,
        tipo_local="REMOTO",
        link_remoto="https://meet.exemplo.com/abc",
    )
    assert banca.tipo_local == "REMOTO"
    assert banca.link_remoto == "https://meet.exemplo.com/abc"
    assert banca.bloco is None and banca.sala is None


def test_defesa_dura_duas_horas(dados_banca, orientador):
    banca = _cadastrar(dados_banca, orientador.usuario)
    assert banca.data_hora_fim - banca.data_hora_inicio == timedelta(hours=2)


def test_convites_guardam_a_data_de_envio(dados_banca, orientador):
    antes = timezone.now()
    banca = _cadastrar(dados_banca, orientador.usuario)
    for convite in banca.convites.all():
        assert convite.enviado_em >= antes
        assert convite.respondido_em is None


def test_tcc_com_banca_nao_recebe_outra(dados_banca, orientador):
    _cadastrar(dados_banca, orientador.usuario)
    with pytest.raises(ValidationError, match="já tem banca"):
        _cadastrar(dados_banca, orientador.usuario)
    assert Banca.objects.count() == 1


def test_tcc_por_publicacao_nao_tem_banca(dados_banca, orientador, tcc):
    TCC.objects.filter(pk=tcc.pk).update(modalidade="PUBLICACAO_APROVADA")
    with pytest.raises(ValidationError, match="publicação"):
        _cadastrar(dados_banca, orientador.usuario)


def test_tcc_fora_de_desenvolvimento_nao_recebe_banca(dados_banca, orientador, tcc):
    TCC.objects.filter(pk=tcc.pk).update(status="APRESENTADO")
    with pytest.raises(ValidationError, match="em desenvolvimento"):
        _cadastrar(dados_banca, orientador.usuario)


def test_falha_na_auditoria_desfaz_a_banca(dados_banca, orientador):
    with (
        mock.patch.object(servico, "registrar", side_effect=RuntimeError("log fora")),
        pytest.raises(RuntimeError),
    ):
        _cadastrar(dados_banca, orientador.usuario)
    assert Banca.objects.count() == 0
    assert ParticipacaoBanca.objects.count() == 0
    assert Convite.objects.count() == 0


# ================================================================== API
def _corpo(dados):
    return {
        "tcc": str(dados["tcc"].pk),
        "titulares": [str(u.pk) for u in dados["titulares"]],
        "suplentes": [str(u.pk) for u in dados["suplentes"]],
        "data_hora_inicio": dados["data_hora_inicio"].isoformat(),
        "tipo_local": dados["tipo_local"],
        "bloco": dados["bloco"],
        "sala": dados["sala"],
    }


def test_post_cria_banca_e_devolve_201(api_como, orientador, dados_banca):
    resp = api_como(orientador.usuario).post(URL, _corpo(dados_banca), format="json")
    assert resp.status_code == 201, resp.data
    assert len(resp.data["participacoes"]) == 4
    assert resp.data["bloco"] == "NUCOMP"
    assert resp.data["sala"] == "10"
    assert resp.data["link_remoto"] is None
    assert resp.data["data_hora_fim"] is not None
    assert all(c["enviado_em"] for c in resp.data["convites"])


def test_post_remota_sem_link_devolve_400_no_campo(api_como, orientador, dados_banca):
    corpo = {**_corpo(dados_banca), "tipo_local": "REMOTO"}
    resp = api_como(orientador.usuario).post(URL, corpo, format="json")
    assert resp.status_code == 400
    assert "link_remoto" in resp.data


def test_post_com_regra_quebrada_devolve_400(api_como, orientador, dados_banca):
    corpo = {**_corpo(dados_banca), "titulares": _corpo(dados_banca)["titulares"][:2]}
    resp = api_como(orientador.usuario).post(URL, corpo, format="json")
    assert resp.status_code == 400
    assert "titulares" in resp.data


def test_secretaria_nao_cria_banca(api_como, criar_usuario, dados_banca):
    resp = api_como(criar_usuario("SECRETARIA")).post(
        URL, _corpo(dados_banca), format="json"
    )
    assert resp.status_code == 403


def test_lista_bancas(api_como, orientador, dados_banca):
    _cadastrar(dados_banca, orientador.usuario)
    resp = api_como(orientador.usuario).get(URL)
    assert resp.status_code == 200
    assert len(resp.data) == 1
