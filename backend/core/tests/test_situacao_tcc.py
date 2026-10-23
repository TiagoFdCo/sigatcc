"""Testes do B7b (situacao do TCC)."""

from unittest import mock

import pytest
from django.http import Http404
from rest_framework.exceptions import ValidationError

from core.models import TCC, HistoricoStatus, LogAuditoria, StatusTCC
from core.services import tcc as servico

pytestmark = pytest.mark.django_db

URL = "/api/tccs/"


def _por_no_status(tcc, status):
    """Monta o cenario direto no banco, sem passar pelo service."""
    extra = {}
    if status == StatusTCC.NAO_APRESENTADO:
        extra["motivo_nao_apresentacao"] = "DESISTENCIA"
    TCC.objects.filter(pk=tcc.pk).update(status=status, **extra)


# ========================================================== B7b: situacao
PERMITIDAS = [
    ("DEFESA_EM_BANCA", "APRESENTADO"),
    ("DEFESA_EM_BANCA", "NAO_APRESENTADO"),
    ("PUBLICACAO_APROVADA", "APROVADO_POR_PUBLICACAO"),
    ("PUBLICACAO_APROVADA", "NAO_APRESENTADO"),
]


@pytest.mark.parametrize("modalidade, para", PERMITIDAS)
def test_transicao_permitida_muda_status_e_grava_historico(
    tcc, orientador, modalidade, para
):
    TCC.objects.filter(pk=tcc.pk).update(modalidade=modalidade)
    servico.mudar_situacao(
        tcc_id=tcc.pk,
        status=para,
        motivo_nao_apresentacao="DESISTENCIA",
        usuario=orientador.usuario,
    )
    tcc.refresh_from_db()
    assert tcc.status == para
    assert HistoricoStatus.objects.filter(tcc=tcc, status=para).exists()
    assert LogAuditoria.objects.filter(
        registro_id=tcc.id, valor_anterior="EM_DESENVOLVIMENTO", valor_novo=para
    ).exists()


PROIBIDAS = [
    (de, para)
    for de in StatusTCC.values
    for para in StatusTCC.values
    if para not in servico.TRANSICOES.get(de, set())
]


@pytest.mark.parametrize("de, para", PROIBIDAS)
def test_transicao_proibida_e_recusada(tcc, orientador, de, para):
    _por_no_status(tcc, de)
    with pytest.raises(ValidationError, match="não permitida"):
        servico.mudar_situacao(
            tcc_id=tcc.pk,
            status=para,
            motivo_nao_apresentacao="DESISTENCIA",
            usuario=orientador.usuario,
        )
    tcc.refresh_from_db()
    assert tcc.status == de


def test_apresentado_exige_modalidade_defesa(tcc, orientador):
    TCC.objects.filter(pk=tcc.pk).update(modalidade="PUBLICACAO_APROVADA")
    with pytest.raises(ValidationError, match="modalidade"):
        servico.mudar_situacao(
            tcc_id=tcc.pk, status="APRESENTADO", usuario=orientador.usuario
        )


@pytest.mark.parametrize("motivo", [None, ""])
def test_nao_apresentado_sem_motivo_e_recusado(tcc, orientador, motivo):
    with pytest.raises(ValidationError, match="motivo_nao_apresentacao"):
        servico.mudar_situacao(
            tcc_id=tcc.pk,
            status="NAO_APRESENTADO",
            motivo_nao_apresentacao=motivo,
            usuario=orientador.usuario,
        )


def test_motivo_outro_exige_descricao(tcc, orientador):
    with pytest.raises(ValidationError, match="motivo_outro"):
        servico.mudar_situacao(
            tcc_id=tcc.pk,
            status="NAO_APRESENTADO",
            motivo_nao_apresentacao="OUTRO",
            usuario=orientador.usuario,
        )


def test_motivo_outro_com_descricao_e_gravado(tcc, orientador):
    servico.mudar_situacao(
        tcc_id=tcc.pk,
        status="NAO_APRESENTADO",
        motivo_nao_apresentacao="OUTRO",
        motivo_outro="Mudou de cidade",
        usuario=orientador.usuario,
    )
    tcc.refresh_from_db()
    assert tcc.motivo_nao_apresentacao == "OUTRO"
    assert tcc.motivo_outro == "Mudou de cidade"


def test_tcc_inativo_nao_muda_de_situacao(tcc, orientador):
    TCC.objects.filter(pk=tcc.pk).update(ativo=False, motivo_inativacao="Desistiu")
    with pytest.raises(ValidationError, match="inativo"):
        servico.mudar_situacao(
            tcc_id=tcc.pk, status="APRESENTADO", usuario=orientador.usuario
        )


def test_tcc_inexistente_da_404(orientador):
    with pytest.raises(Http404):
        servico.mudar_situacao(
            tcc_id="00000000-0000-0000-0000-000000000000",
            status="APRESENTADO",
            usuario=orientador.usuario,
        )


def test_falha_na_auditoria_desfaz_a_mudanca(tcc, orientador):
    with (
        mock.patch.object(servico, "registrar", side_effect=RuntimeError("log fora")),
        pytest.raises(RuntimeError),
    ):
        servico.mudar_situacao(
            tcc_id=tcc.pk, status="APRESENTADO", usuario=orientador.usuario
        )
    tcc.refresh_from_db()
    assert tcc.status == StatusTCC.EM_DESENVOLVIMENTO
    assert HistoricoStatus.objects.filter(tcc=tcc).count() == 1


# ================================================================== API
def test_post_situacao_devolve_200(api_como, orientador, tcc):
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc.pk}/situacao/", {"status": "APRESENTADO"}, format="json"
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["status"] == "APRESENTADO"


def test_post_situacao_invalida_devolve_400(api_como, orientador, tcc):
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc.pk}/situacao/", {"status": "NAO_APRESENTADO"}, format="json"
    )
    assert resp.status_code == 400
