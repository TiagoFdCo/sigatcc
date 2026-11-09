"""Testes da C1 (aprovacao por publicacao)."""

from datetime import timedelta
from unittest import mock

import pytest
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import (
    TCC,
    HistoricoStatus,
    LogAuditoria,
    Publicacao,
    StatusTCC,
    TipoUsuario,
)
from core.services import banca as servico_banca
from core.services import publicacao as servico
from core.services import tcc as servico_tcc
from core.validators import issn_valido, validar_issn_doi

pytestmark = pytest.mark.django_db

URL = "/api/tccs/"
ID_INEXISTENTE = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
def tcc_pub(tcc):
    """O TCC da fixture, na modalidade publicacao."""
    TCC.objects.filter(pk=tcc.pk).update(modalidade="PUBLICACAO_APROVADA")
    tcc.refresh_from_db()
    return tcc


@pytest.fixture
def dados_pub():
    return {
        "periodico": "Revista Brasileira de Informática na Educação",
        "issn_doi": "10.5753/rbie.2026.1234",
        "data_publicacao": timezone.localdate() - timedelta(days=10),
        "comprovante_arquivo_path": "comprovantes/rbie-2026.pdf",
        "link_artigo": "https://example.org/artigo",
    }


def _json(dados):
    """A data vai como texto ISO no corpo da requisicao."""
    return {**dados, "data_publicacao": dados["data_publicacao"].isoformat()}


def _nada_mudou(tcc):
    tcc.refresh_from_db()
    assert tcc.status == StatusTCC.EM_DESENVOLVIMENTO
    assert not Publicacao.objects.filter(tcc=tcc).exists()
    assert HistoricoStatus.objects.filter(tcc=tcc).count() == 1


# ================================================================ servico
def test_registrar_publicacao_aprova_o_tcc(tcc_pub, dados_pub, orientador):
    resultado = servico.registrar_publicacao(
        tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
    )

    assert resultado.status == StatusTCC.APROVADO_POR_PUBLICACAO
    pub = Publicacao.objects.get(tcc=tcc_pub)
    assert pub.periodico == dados_pub["periodico"]
    assert pub.issn_doi == dados_pub["issn_doi"]
    assert pub.data_publicacao == dados_pub["data_publicacao"]
    assert pub.comprovante_arquivo_path == dados_pub["comprovante_arquivo_path"]
    assert pub.link_artigo == dados_pub["link_artigo"]


def test_registrar_publicacao_grava_historico_e_auditoria(
    tcc_pub, dados_pub, orientador
):
    servico.registrar_publicacao(
        tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
    )

    pub = Publicacao.objects.get(tcc=tcc_pub)
    historico = HistoricoStatus.objects.get(
        tcc=tcc_pub, status=StatusTCC.APROVADO_POR_PUBLICACAO
    )
    assert dados_pub["periodico"] in historico.justificativa
    assert LogAuditoria.objects.filter(
        entidade="PUBLICACAO",
        registro_id=pub.id,
        campo="tcc",
        valor_novo=str(tcc_pub.pk),
        responsavel=orientador.usuario,
    ).exists()
    assert LogAuditoria.objects.filter(
        entidade="TCC",
        registro_id=tcc_pub.id,
        valor_anterior="EM_DESENVOLVIMENTO",
        valor_novo="APROVADO_POR_PUBLICACAO",
    ).exists()


def test_espacos_das_bordas_saem_e_link_vazio_vira_nulo(tcc_pub, dados_pub, orientador):
    servico.registrar_publicacao(
        tcc_id=tcc_pub.pk,
        dados={**dados_pub, "periodico": "  Revista X  ", "link_artigo": ""},
        usuario=orientador.usuario,
    )
    pub = Publicacao.objects.get(tcc=tcc_pub)
    assert pub.periodico == "Revista X"
    assert pub.link_artigo is None


@pytest.mark.parametrize(
    "campo", ["periodico", "issn_doi", "data_publicacao", "comprovante_arquivo_path"]
)
@pytest.mark.parametrize("vazio", [None, "", "   "])
def test_campo_obrigatorio_em_branco_e_recusado(
    tcc_pub, dados_pub, orientador, campo, vazio
):
    if campo == "data_publicacao" and vazio == "   ":
        vazio = None  # data nao tem "so espacos"
    with pytest.raises(ValidationError, match=campo):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk,
            dados={**dados_pub, campo: vazio},
            usuario=orientador.usuario,
        )
    _nada_mudou(tcc_pub)


def test_data_futura_e_recusada(tcc_pub, dados_pub, orientador):
    dados = {**dados_pub, "data_publicacao": timezone.localdate() + timedelta(days=2)}
    with pytest.raises(ValidationError, match="futura"):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk, dados=dados, usuario=orientador.usuario
        )
    _nada_mudou(tcc_pub)


def test_data_de_hoje_e_aceita(tcc_pub, dados_pub, orientador):
    dados = {**dados_pub, "data_publicacao": timezone.localdate()}
    servico.registrar_publicacao(
        tcc_id=tcc_pub.pk, dados=dados, usuario=orientador.usuario
    )
    assert Publicacao.objects.filter(tcc=tcc_pub).exists()


def test_modalidade_defesa_nao_recebe_publicacao(tcc, dados_pub, orientador):
    # a fixture `tcc` e de defesa em banca (RD07, RD08)
    with pytest.raises(ValidationError, match="Publicação aprovada"):
        servico.registrar_publicacao(
            tcc_id=tcc.pk, dados=dados_pub, usuario=orientador.usuario
        )
    _nada_mudou(tcc)


def test_tcc_fora_de_desenvolvimento_e_recusado(tcc_pub, dados_pub, orientador):
    TCC.objects.filter(pk=tcc_pub.pk).update(
        status="NAO_APRESENTADO", motivo_nao_apresentacao="DESISTENCIA"
    )
    with pytest.raises(ValidationError, match="em desenvolvimento"):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
        )
    assert not Publicacao.objects.filter(tcc=tcc_pub).exists()


def test_tcc_inativo_e_recusado(tcc_pub, dados_pub, orientador):
    TCC.objects.filter(pk=tcc_pub.pk).update(ativo=False, motivo_inativacao="Desistiu")
    with pytest.raises(ValidationError, match="inativo"):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
        )
    assert not Publicacao.objects.filter(tcc=tcc_pub).exists()


def test_segunda_publicacao_e_recusada(tcc_pub, dados_pub, orientador):
    Publicacao.objects.create(
        tcc=tcc_pub,
        periodico="Outro periódico",
        issn_doi="1234-5678",
        data_publicacao=timezone.localdate() - timedelta(days=30),
        comprovante_arquivo_path="comprovantes/outro.pdf",
    )
    with pytest.raises(ValidationError, match="já tem publicação"):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
        )
    assert Publicacao.objects.filter(tcc=tcc_pub).count() == 1


def test_registrar_duas_vezes_nao_duplica(tcc_pub, dados_pub, orientador):
    servico.registrar_publicacao(
        tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
    )
    with pytest.raises(ValidationError):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
        )
    assert Publicacao.objects.filter(tcc=tcc_pub).count() == 1


def test_tcc_inexistente_da_404(dados_pub, orientador):
    with pytest.raises(Http404):
        servico.registrar_publicacao(
            tcc_id=ID_INEXISTENTE, dados=dados_pub, usuario=orientador.usuario
        )


def test_falha_na_auditoria_da_publicacao_desfaz_tudo(tcc_pub, dados_pub, orientador):
    with (
        mock.patch.object(servico, "registrar", side_effect=RuntimeError("log fora")),
        pytest.raises(RuntimeError),
    ):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
        )
    _nada_mudou(tcc_pub)


def test_falha_na_mudanca_de_situacao_desfaz_a_publicacao(
    tcc_pub, dados_pub, orientador
):
    with (
        mock.patch.object(
            servico_tcc, "registrar", side_effect=RuntimeError("log fora")
        ),
        pytest.raises(RuntimeError),
    ):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
        )
    _nada_mudou(tcc_pub)


# ------------------------------------------- regras ligadas em tcc.py (C1)
def test_aprovar_por_publicacao_sem_publicacao_e_recusado(tcc_pub, orientador):
    with pytest.raises(ValidationError, match="Registre a publicação"):
        servico_tcc.mudar_situacao(
            tcc_id=tcc_pub.pk,
            status="APROVADO_POR_PUBLICACAO",
            usuario=orientador.usuario,
        )
    tcc_pub.refresh_from_db()
    assert tcc_pub.status == StatusTCC.EM_DESENVOLVIMENTO


def test_mudar_situacao_aceita_quando_a_publicacao_existe(tcc_pub, orientador):
    Publicacao.objects.create(
        tcc=tcc_pub,
        periodico="Periódico",
        issn_doi="1234-5678",
        data_publicacao=timezone.localdate() - timedelta(days=5),
        comprovante_arquivo_path="comprovantes/p.pdf",
    )
    servico_tcc.mudar_situacao(
        tcc_id=tcc_pub.pk, status="APROVADO_POR_PUBLICACAO", usuario=orientador.usuario
    )
    tcc_pub.refresh_from_db()
    assert tcc_pub.status == StatusTCC.APROVADO_POR_PUBLICACAO


def test_modalidade_nao_muda_com_publicacao_registrada(tcc_pub, dados_pub, orientador):
    servico.registrar_publicacao(
        tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
    )
    with pytest.raises(ValidationError, match="modalidade"):
        servico_tcc.atualizar_tcc(
            tcc_id=tcc_pub.pk,
            dados={"modalidade": "DEFESA_EM_BANCA"},
            usuario=orientador.usuario,
        )
    tcc_pub.refresh_from_db()
    assert tcc_pub.modalidade == "PUBLICACAO_APROVADA"


def test_editar_outros_campos_com_publicacao_continua_valendo(
    tcc_pub, dados_pub, orientador
):
    servico.registrar_publicacao(
        tcc_id=tcc_pub.pk, dados=dados_pub, usuario=orientador.usuario
    )
    servico_tcc.atualizar_tcc(
        tcc_id=tcc_pub.pk,
        dados={"titulo": "Título corrigido", "modalidade": "PUBLICACAO_APROVADA"},
        usuario=orientador.usuario,
    )
    tcc_pub.refresh_from_db()
    assert tcc_pub.titulo == "Título corrigido"


# ================================================================== API
def test_post_publicacao_devolve_201_com_o_tcc_aprovado(
    api_como, orientador, tcc_pub, dados_pub
):
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc_pub.pk}/publicacao/", _json(dados_pub), format="json"
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "APROVADO_POR_PUBLICACAO"
    assert resp.data["publicacao"]["issn_doi"] == dados_pub["issn_doi"]
    assert resp.data["publicacao"]["data_publicacao"] == (
        dados_pub["data_publicacao"].isoformat()
    )


def test_detalhe_traz_a_publicacao_so_depois_de_registrada(
    api_como, orientador, tcc_pub, dados_pub
):
    cliente = api_como(orientador.usuario)
    assert cliente.get(f"{URL}{tcc_pub.pk}/").data["publicacao"] is None

    cliente.post(f"{URL}{tcc_pub.pk}/publicacao/", _json(dados_pub), format="json")

    detalhe = cliente.get(f"{URL}{tcc_pub.pk}/").data
    assert detalhe["publicacao"]["periodico"] == dados_pub["periodico"]


def test_post_publicacao_sem_campos_devolve_400_por_campo(
    api_como, orientador, tcc_pub
):
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc_pub.pk}/publicacao/", {}, format="json"
    )
    assert resp.status_code == 400
    assert {
        "periodico",
        "issn_doi",
        "data_publicacao",
        "comprovante_arquivo_path",
    } <= set(resp.data)


def test_post_publicacao_com_link_invalido_devolve_400(
    api_como, orientador, tcc_pub, dados_pub
):
    corpo = {**_json(dados_pub), "link_artigo": "isso-nao-e-um-link"}
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc_pub.pk}/publicacao/", corpo, format="json"
    )
    assert resp.status_code == 400
    assert "link_artigo" in resp.data


def test_post_publicacao_em_tcc_de_defesa_devolve_400(
    api_como, orientador, tcc, dados_pub
):
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc.pk}/publicacao/", _json(dados_pub), format="json"
    )
    assert resp.status_code == 400


def test_post_publicacao_de_tcc_inexistente_devolve_404(
    api_como, orientador, dados_pub
):
    resp = api_como(orientador.usuario).post(
        f"{URL}{ID_INEXISTENTE}/publicacao/", _json(dados_pub), format="json"
    )
    assert resp.status_code == 404


def test_secretaria_nao_registra_publicacao(
    api_como, criar_usuario, tcc_pub, dados_pub
):
    secretaria = criar_usuario(TipoUsuario.SECRETARIA)
    resp = api_como(secretaria).post(
        f"{URL}{tcc_pub.pk}/publicacao/", _json(dados_pub), format="json"
    )
    assert resp.status_code == 403
    assert not Publicacao.objects.filter(tcc=tcc_pub).exists()


def test_sem_login_devolve_401(api, tcc_pub, dados_pub):
    resp = api.post(f"{URL}{tcc_pub.pk}/publicacao/", _json(dados_pub), format="json")
    assert resp.status_code == 401


def test_rota_de_situacao_nao_aprova_sem_publicacao(api_como, orientador, tcc_pub):
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc_pub.pk}/situacao/",
        {"status": "APROVADO_POR_PUBLICACAO"},
        format="json",
    )
    assert resp.status_code == 400
    assert "Registre a publicação" in str(resp.data)


# ============================================ ISSN/DOI (RBN34) e banca (RD07)
@pytest.mark.parametrize(
    "valor",
    ["10.5753/rbie.2026.1234", "10.1000/xyz123", "0378-5955", "2049-3630", "0000-006X"],
)
def test_issn_doi_validos_sao_aceitos(tcc_pub, dados_pub, orientador, valor):
    servico.registrar_publicacao(
        tcc_id=tcc_pub.pk,
        dados={**dados_pub, "issn_doi": valor},
        usuario=orientador.usuario,
    )
    assert Publicacao.objects.get(tcc=tcc_pub).issn_doi == valor


@pytest.mark.parametrize(
    "valor",
    [
        "abc",
        "12345",
        "10.12/curto",  # prefixo do DOI com menos de 4 digitos
        "10.5753/",  # sem sufixo
        "10.5753/com espaco",
        "0378-5956",  # digito verificador errado
        "03785955",  # sem hifen
        "0378-59555",
        "https://example.org/artigo",
    ],
)
def test_issn_doi_invalido_e_recusado(tcc_pub, dados_pub, orientador, valor):
    with pytest.raises(ValidationError, match="issn_doi"):
        servico.registrar_publicacao(
            tcc_id=tcc_pub.pk,
            dados={**dados_pub, "issn_doi": valor},
            usuario=orientador.usuario,
        )
    _nada_mudou(tcc_pub)


def test_issn_com_x_minusculo_e_normalizado():
    assert validar_issn_doi("0000-006x") == "0000-006X"
    assert issn_valido("0000-006X")


def test_post_com_doi_invalido_devolve_400_no_campo(
    api_como, orientador, tcc_pub, dados_pub
):
    resposta = api_como(orientador.usuario).post(
        f"{URL}{tcc_pub.pk}/publicacao/",
        {**_json(dados_pub), "issn_doi": "nao-e-doi"},
        format="json",
    )
    assert resposta.status_code == 400
    assert "issn_doi" in resposta.json()
    _nada_mudou(tcc_pub)


def test_tcc_com_banca_nao_recebe_publicacao(tcc, dados_banca, dados_pub, orientador):
    """RD07: banca cadastrada e depois troca de modalidade nao abre a brecha."""
    servico_banca.cadastrar_banca(**dados_banca, usuario=orientador.usuario)
    TCC.objects.filter(pk=tcc.pk).update(modalidade="PUBLICACAO_APROVADA")
    with pytest.raises(ValidationError, match="banca"):
        servico.registrar_publicacao(
            tcc_id=tcc.pk, dados=dados_pub, usuario=orientador.usuario
        )
    _nada_mudou(tcc)


def test_modalidade_nao_muda_com_banca_cadastrada(tcc, dados_banca, orientador):
    servico_banca.cadastrar_banca(**dados_banca, usuario=orientador.usuario)
    with pytest.raises(ValidationError, match="modalidade"):
        servico_tcc.atualizar_tcc(
            tcc_id=tcc.pk,
            dados={"modalidade": "PUBLICACAO_APROVADA"},
            usuario=orientador.usuario,
        )
    tcc.refresh_from_db()
    assert tcc.modalidade == "DEFESA_EM_BANCA"


def test_patch_nao_troca_modalidade_de_tcc_com_banca_nem_permite_publicar(
    api_como, tcc, dados_banca, dados_pub, orientador
):
    """O cenario do revisor, de ponta a ponta pela API."""
    servico_banca.cadastrar_banca(**dados_banca, usuario=orientador.usuario)
    cliente = api_como(orientador.usuario)
    patch = cliente.patch(
        f"{URL}{tcc.pk}/", {"modalidade": "PUBLICACAO_APROVADA"}, format="json"
    )
    assert patch.status_code == 400
    assert "modalidade" in patch.json()
    post = cliente.post(f"{URL}{tcc.pk}/publicacao/", _json(dados_pub), format="json")
    assert post.status_code == 400
    assert not Publicacao.objects.filter(tcc=tcc).exists()
