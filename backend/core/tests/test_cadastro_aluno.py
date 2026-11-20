"""Testes da C2a: confirmacao do cadastro do aluno pelo Professor de TCC (RBN61)."""

from unittest import mock

import pytest
from rest_framework.exceptions import PermissionDenied

from core.models import Aluno, LogAcesso, LogAuditoria
from core.services import pessoas as servico_pessoas

pytestmark = pytest.mark.django_db

SENHA = "senha-forte-123"  # a que o conftest usa em criar_usuario
LOGIN = "/api/auth/login/"


@pytest.fixture
def professor_tcc(criar_docente):
    docente = criar_docente()
    docente.professor_tcc = True
    docente.save(update_fields=["professor_tcc"])
    return docente


def _url(aluno, acao):
    return f"/api/alunos/{aluno.pk}/{acao}/"


def _logs(aluno, campo):
    return LogAuditoria.objects.filter(
        entidade="ALUNO", registro_id=aluno.pk, campo=campo
    )


def _entrar(api, aluno, senha=SENHA):
    return api.post(
        LOGIN, {"login": aluno.usuario.email, "senha": senha}, format="json"
    )


# ================================================================ confirmar
def test_professor_confirma_o_cadastro(api_como, professor_tcc, aluno):
    assert aluno.cadastro_confirmado is False

    resp = api_como(professor_tcc.usuario).post(_url(aluno, "confirmar"))

    assert resp.status_code == 200, resp.data
    assert resp.data["cadastro_confirmado"] is True
    aluno.refresh_from_db()
    assert aluno.cadastro_confirmado is True
    (log,) = _logs(aluno, "cadastro_confirmado")
    assert log.responsavel == professor_tcc.usuario
    assert (log.valor_anterior, log.valor_novo) == ("False", "True")


def test_confirmar_de_novo_e_recusado(api_como, professor_tcc, aluno):
    cliente = api_como(professor_tcc.usuario)
    cliente.post(_url(aluno, "confirmar"))

    resp = cliente.post(_url(aluno, "confirmar"))

    assert resp.status_code == 400
    assert "cadastro" in resp.data
    assert _logs(aluno, "cadastro_confirmado").count() == 1


def test_so_o_professor_de_tcc_confirma(
    api_como, api, orientador, criar_usuario, aluno
):
    """Docente comum, administrador, secretaria e o proprio aluno nao confirmam."""
    for quem in (
        orientador.usuario,
        criar_usuario("ADMINISTRADOR"),
        criar_usuario("SECRETARIA"),
        aluno.usuario,
    ):
        for acao in ("confirmar", "recusar"):
            resp = api_como(quem).post(
                _url(aluno, acao), {"motivo": "x"}, format="json"
            )
            assert resp.status_code == 403, (quem.tipo_usuario, acao)
    api.force_authenticate(user=None)
    assert api.post(_url(aluno, "confirmar")).status_code == 401
    aluno.refresh_from_db()
    assert aluno.cadastro_confirmado is False
    assert not LogAuditoria.objects.filter(campo="cadastro_confirmado").exists()


def test_professor_de_tcc_inativo_nao_confirma(api_como, professor_tcc, aluno):
    professor_tcc.usuario.ativo = False
    professor_tcc.usuario.save(update_fields=["ativo"])
    resp = api_como(professor_tcc.usuario).post(_url(aluno, "confirmar"))
    assert resp.status_code == 403


def test_servico_tambem_exige_professor_de_tcc(orientador, aluno):
    """A regra vale para quem chamar o servico, nao so pela API."""
    with pytest.raises(PermissionDenied):
        servico_pessoas.confirmar_cadastro_aluno(
            aluno_id=aluno.pk, usuario=orientador.usuario
        )


def test_aluno_inativo_nao_tem_cadastro_a_decidir(api_como, professor_tcc, aluno):
    aluno.usuario.ativo = False
    aluno.usuario.save(update_fields=["ativo"])
    resp = api_como(professor_tcc.usuario).post(_url(aluno, "confirmar"))
    assert resp.status_code == 400
    assert "aluno" in resp.data


def test_confirmar_aluno_inexistente_da_404(api_como, professor_tcc):
    resp = api_como(professor_tcc.usuario).post(
        "/api/alunos/00000000-0000-0000-0000-000000000000/confirmar/"
    )
    assert resp.status_code == 404


def test_falha_na_auditoria_desfaz_a_confirmacao(professor_tcc, aluno):
    with (
        mock.patch(
            "core.services.pessoas.registrar", side_effect=RuntimeError("log fora")
        ),
        pytest.raises(RuntimeError),
    ):
        servico_pessoas.confirmar_cadastro_aluno(
            aluno_id=aluno.pk, usuario=professor_tcc.usuario
        )
    aluno.refresh_from_db()
    assert aluno.cadastro_confirmado is False


# ================================================================== recusar
def test_recusa_exige_motivo(api_como, professor_tcc, aluno):
    cliente = api_como(professor_tcc.usuario)
    for corpo in ({}, {"motivo": ""}, {"motivo": "   "}):
        resp = cliente.post(_url(aluno, "recusar"), corpo, format="json")
        assert resp.status_code == 400, corpo
        assert "motivo" in resp.data
    assert not _logs(aluno, "cadastro_recusado").exists()


def test_recusa_grava_o_motivo_e_mantem_o_cadastro_pendente(
    api_como, professor_tcc, aluno
):
    resp = api_como(professor_tcc.usuario).post(
        _url(aluno, "recusar"),
        {"motivo": "  Matrícula não consta no curso  "},
        format="json",
    )

    assert resp.status_code == 200, resp.data
    assert resp.data["cadastro_confirmado"] is False
    (log,) = _logs(aluno, "cadastro_recusado")
    assert log.responsavel == professor_tcc.usuario
    assert log.valor_novo == "Matrícula não consta no curso"
    aluno.refresh_from_db()
    assert aluno.cadastro_confirmado is False


def test_cadastro_ja_confirmado_nao_pode_ser_recusado(api_como, professor_tcc, aluno):
    cliente = api_como(professor_tcc.usuario)
    cliente.post(_url(aluno, "confirmar"))

    resp = cliente.post(_url(aluno, "recusar"), {"motivo": "x"}, format="json")

    assert resp.status_code == 400
    aluno.refresh_from_db()
    assert aluno.cadastro_confirmado is True


# ======================================================== fila de pendentes
def test_lista_filtra_cadastros_pendentes(api_como, professor_tcc, criar_aluno):
    pendente, confirmado = criar_aluno(), criar_aluno()
    Aluno.objects.filter(pk=confirmado.pk).update(cadastro_confirmado=True)
    cliente = api_como(professor_tcc.usuario)

    fila = cliente.get("/api/alunos/", {"cadastro": "pendente"}).data
    feitos = cliente.get("/api/alunos/", {"cadastro": "confirmado"}).data

    assert [a["id"] for a in fila] == [str(pendente.pk)]
    assert [a["id"] for a in feitos] == [str(confirmado.pk)]


# ============================================ login so com cadastro confirmado
def test_aluno_com_cadastro_pendente_nao_entra(api, aluno):
    resp = _entrar(api, aluno)

    assert resp.status_code == 403
    assert resp.data["code"] == "cadastro_nao_confirmado"
    assert "Professor de TCC" in resp.data["detail"]
    assert "access" not in resp.data
    assert not LogAcesso.objects.filter(usuario=aluno.usuario).exists()


def test_aluno_entra_depois_da_confirmacao(api, api_como, professor_tcc, aluno):
    api_como(professor_tcc.usuario).post(_url(aluno, "confirmar"))
    api.force_authenticate(user=None)

    resp = _entrar(api, aluno)

    assert resp.status_code == 200, resp.data
    assert resp.data["usuario"]["tipo_usuario"] == "ALUNO"
    assert LogAcesso.objects.filter(usuario=aluno.usuario).count() == 1


def test_senha_errada_nao_revela_o_estado_do_cadastro(api, aluno):
    """Quem nao sabe a senha recebe a mesma resposta de qualquer login invalido."""
    resp = _entrar(api, aluno, senha="outra-senha-errada")
    assert resp.status_code == 401
    assert resp.data["code"] == "credenciais_invalidas"


def test_recusa_nao_libera_o_login(api, api_como, professor_tcc, aluno):
    api_como(professor_tcc.usuario).post(
        _url(aluno, "recusar"), {"motivo": "Dados incorretos"}, format="json"
    )
    api.force_authenticate(user=None)
    assert _entrar(api, aluno).status_code == 403


def test_outros_perfis_nao_dependem_da_confirmacao(api, orientador):
    resp = api.post(
        LOGIN,
        {"login": orientador.usuario.email, "senha": SENHA},
        format="json",
    )
    assert resp.status_code == 200
