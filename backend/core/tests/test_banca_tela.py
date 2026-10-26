"""Testes do que a interface de banca (B9c) usa da API."""

import pytest

from core.services import banca as servico_banca

pytestmark = pytest.mark.django_db


def test_detalhe_do_tcc_sem_banca(api_como, orientador, tcc):
    resp = api_como(orientador.usuario).get(f"/api/tccs/{tcc.pk}/")
    assert resp.data["banca"] is None


def test_detalhe_do_tcc_traz_a_banca_com_nomes_e_convites(
    api_como, orientador, tcc, dados_banca
):
    servico_banca.cadastrar_banca(**dados_banca, usuario=orientador.usuario)

    banca = api_como(orientador.usuario).get(f"/api/tccs/{tcc.pk}/").data["banca"]

    assert banca["tipo_local"] == "PRESENCIAL"
    nomes = {p["usuario_nome"] for p in banca["participacoes"]}
    assert orientador.usuario.nome_completo in nomes
    assert {p["tipo_usuario"] for p in banca["participacoes"]} == {"DOCENTE"}
    assert len(banca["convites"]) == 3
    assert {c["status"] for c in banca["convites"]} == {"PENDENTE"}


def test_listagem_de_bancas_traz_o_titulo_do_tcc(
    api_como, orientador, tcc, dados_banca
):
    servico_banca.cadastrar_banca(**dados_banca, usuario=orientador.usuario)
    resp = api_como(orientador.usuario).get("/api/bancas/")
    assert resp.data[0]["tcc_titulo"] == tcc.titulo
