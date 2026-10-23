"""Testes do B7a (cadastro e edicao de TCC)."""

from unittest import mock

import pytest
from rest_framework.exceptions import ValidationError

from core.models import TCC, HistoricoStatus, LogAuditoria, StatusTCC
from core.services import tcc as servico

pytestmark = pytest.mark.django_db

URL = "/api/tccs/"


# ============================================================ B7a: cadastro
def test_cadastro_grava_tcc_historico_e_auditoria(dados_tcc, orientador, aluno):
    tcc = servico.cadastrar_tcc(dados=dados_tcc, usuario=orientador.usuario)

    assert tcc.status == StatusTCC.EM_DESENVOLVIMENTO
    assert tcc.curso == aluno.curso
    hist = HistoricoStatus.objects.get(tcc=tcc)
    assert hist.status == StatusTCC.EM_DESENVOLVIMENTO
    log = LogAuditoria.objects.get(entidade="TCC", registro_id=tcc.id)
    assert log.responsavel == orientador.usuario
    assert log.valor_anterior is None and log.valor_novo == "EM_DESENVOLVIMENTO"


def test_orientador_inativo_e_recusado(dados_tcc, criar_docente):
    inativo = criar_docente(ativo=False)
    with pytest.raises(ValidationError, match="orientador está inativo"):
        servico.cadastrar_tcc(
            dados={**dados_tcc, "orientador": inativo}, usuario=inativo.usuario
        )
    assert TCC.objects.count() == 0


def test_coorientador_igual_ao_orientador_e_recusado(dados_tcc, orientador):
    with pytest.raises(ValidationError, match="diferente do orientador"):
        servico.cadastrar_tcc(
            dados={**dados_tcc, "coorientador": orientador}, usuario=orientador.usuario
        )


def test_coorientador_inativo_e_recusado(dados_tcc, orientador, criar_docente):
    with pytest.raises(ValidationError, match="coorientador está inativo"):
        servico.cadastrar_tcc(
            dados={**dados_tcc, "coorientador": criar_docente(ativo=False)},
            usuario=orientador.usuario,
        )


def test_coorientador_diferente_e_aceito(dados_tcc, orientador, criar_docente):
    co = criar_docente()
    tcc = servico.cadastrar_tcc(
        dados={**dados_tcc, "coorientador": co}, usuario=orientador.usuario
    )
    assert tcc.coorientador == co


def test_segundo_tcc_ativo_do_mesmo_aluno_e_recusado(tcc, dados_tcc, orientador):
    with pytest.raises(ValidationError, match="já tem um TCC ativo"):
        servico.cadastrar_tcc(dados=dados_tcc, usuario=orientador.usuario)
    assert TCC.objects.count() == 1


def test_tcc_inativo_nao_impede_novo_cadastro(tcc, dados_tcc, orientador):
    TCC.objects.filter(pk=tcc.pk).update(ativo=False, motivo_inativacao="Troca de tema")
    servico.cadastrar_tcc(dados=dados_tcc, usuario=orientador.usuario)
    assert TCC.objects.filter(ativo=True).count() == 1


def test_falha_na_auditoria_desfaz_o_cadastro(dados_tcc, orientador):
    with (
        mock.patch.object(servico, "registrar", side_effect=RuntimeError("log fora")),
        pytest.raises(RuntimeError),
    ):
        servico.cadastrar_tcc(dados=dados_tcc, usuario=orientador.usuario)
    assert TCC.objects.count() == 0
    assert HistoricoStatus.objects.count() == 0


# ======================================================== B7a: edicao (PATCH)
def test_edicao_grava_um_log_por_campo_alterado(tcc, orientador):
    servico.atualizar_tcc(
        tcc_id=tcc.pk,
        dados={"titulo": "Novo titulo", "subtitulo": tcc.subtitulo},
        usuario=orientador.usuario,
    )
    tcc.refresh_from_db()
    assert tcc.titulo == "Novo titulo"
    logs = LogAuditoria.objects.filter(registro_id=tcc.id, campo="titulo")
    assert logs.count() == 1
    assert not LogAuditoria.objects.filter(
        registro_id=tcc.id, campo="subtitulo"
    ).exists()


def test_edicao_nao_troca_o_autor(tcc, orientador, criar_aluno):
    with pytest.raises(ValidationError, match="autor"):
        servico.atualizar_tcc(
            tcc_id=tcc.pk, dados={"autor": criar_aluno()}, usuario=orientador.usuario
        )


def test_edicao_aplica_regra_do_coorientador(tcc, orientador):
    with pytest.raises(ValidationError, match="diferente do orientador"):
        servico.atualizar_tcc(
            tcc_id=tcc.pk,
            dados={"coorientador": orientador},
            usuario=orientador.usuario,
        )


# ================================================================== API
def _corpo(aluno, orientador, area, **extra):
    return {
        "titulo": "Sistema",
        "area_conhecimento": str(area.pk),
        "modalidade": "DEFESA_EM_BANCA",
        "autor": str(aluno.pk),
        "orientador": str(orientador.pk),
        **extra,
    }


def test_post_cria_tcc_e_devolve_201(api_como, orientador, aluno, area):
    resp = api_como(orientador.usuario).post(
        URL, _corpo(aluno, orientador, area), format="json"
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "EM_DESENVOLVIMENTO"
    assert resp.data["curso"] == aluno.curso.pk


def test_post_com_regra_quebrada_devolve_400(api_como, orientador, aluno, area):
    corpo = _corpo(aluno, orientador, area, coorientador=str(orientador.pk))
    resp = api_como(orientador.usuario).post(URL, corpo, format="json")
    assert resp.status_code == 400
    assert "coorientador" in resp.data


def test_sem_login_nao_cria(api, orientador, aluno, area):
    resp = api.post(URL, _corpo(aluno, orientador, area), format="json")
    assert resp.status_code in (401, 403)
    assert TCC.objects.count() == 0


def test_secretaria_lista_mas_nao_cria(api_como, criar_usuario, tcc, orientador, area):
    cliente = api_como(criar_usuario("SECRETARIA"))
    assert cliente.get(URL).status_code == 200
    resp = cliente.post(URL, _corpo(tcc.autor, orientador, area), format="json")
    assert resp.status_code == 403


def test_patch_nao_altera_status(api_como, orientador, tcc):
    resp = api_como(orientador.usuario).patch(
        f"{URL}{tcc.pk}/", {"status": "APRESENTADO"}, format="json"
    )
    assert resp.status_code == 200
    tcc.refresh_from_db()
    assert tcc.status == StatusTCC.EM_DESENVOLVIMENTO


def test_patch_altera_titulo(api_como, orientador, tcc):
    resp = api_como(orientador.usuario).patch(
        f"{URL}{tcc.pk}/", {"titulo": "Outro"}, format="json"
    )
    assert resp.status_code == 200
    assert resp.data["titulo"] == "Outro"


def test_delete_nao_existe(api_como, orientador, tcc):
    resp = api_como(orientador.usuario).delete(f"{URL}{tcc.pk}/")
    assert resp.status_code == 405
