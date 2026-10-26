"""Testes do B5 (login JWT, bloqueio por tentativas, LOG_ACESSO, sessao)."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import LogAcesso
from core.services.acesso import MAX_TENTATIVAS
from core.validators import SenhaForteValidator

pytestmark = pytest.mark.django_db

SENHA = "senha-forte-123"  # a senha que o conftest usa em criar_usuario
LOGIN = "/api/auth/login/"
REFRESH = "/api/auth/refresh/"
LOGOUT = "/api/auth/logout/"
ME = "/api/auth/me/"


def _entrar(api, login, senha=SENHA):
    return api.post(LOGIN, {"login": login, "senha": senha}, format="json")


# =============================================================== login
def test_login_por_email_devolve_tokens_e_grava_acesso(api, orientador):
    resp = _entrar(api, orientador.usuario.email)

    assert resp.status_code == 200, resp.data
    assert resp.data["access"] and resp.data["refresh"]
    assert resp.data["usuario"]["tipo_usuario"] == "DOCENTE"
    acesso = LogAcesso.objects.get(usuario=orientador.usuario)
    assert acesso.ip == "127.0.0.1"


def test_login_por_matricula_institucional(api, orientador):
    resp = _entrar(api, orientador.matricula_institucional)
    assert resp.status_code == 200


def test_email_nao_diferencia_maiusculas(api, orientador):
    resp = _entrar(api, orientador.usuario.email.upper())
    assert resp.status_code == 200


def test_senha_errada_devolve_401_e_conta_tentativa(api, orientador):
    resp = _entrar(api, orientador.usuario.email, "errada")

    assert resp.status_code == 401
    assert resp.data["code"] == "credenciais_invalidas"
    orientador.usuario.refresh_from_db()
    assert orientador.usuario.tentativas_falhas == 1
    assert not LogAcesso.objects.exists()


def test_quinta_tentativa_errada_bloqueia_por_15_minutos(api, orientador):
    email = orientador.usuario.email
    for _ in range(MAX_TENTATIVAS - 1):
        assert _entrar(api, email, "errada").status_code == 401

    resp = _entrar(api, email, "errada")

    assert resp.status_code == 423
    assert resp.data["code"] == "conta_bloqueada"
    orientador.usuario.refresh_from_db()
    restante = orientador.usuario.bloqueado_ate - timezone.now()
    assert timedelta(minutes=14) < restante <= timedelta(minutes=15)


def test_conta_bloqueada_recusa_ate_a_senha_certa(api, orientador):
    usuario = orientador.usuario
    usuario.bloqueado_ate = timezone.now() + timedelta(minutes=10)
    usuario.save()
    assert _entrar(api, usuario.email).status_code == 423


def test_bloqueio_vencido_libera_e_zera_o_contador(api, orientador):
    usuario = orientador.usuario
    usuario.bloqueado_ate = timezone.now() - timedelta(minutes=1)
    usuario.tentativas_falhas = 3
    usuario.save()

    assert _entrar(api, usuario.email).status_code == 200
    usuario.refresh_from_db()
    assert usuario.tentativas_falhas == 0
    assert usuario.bloqueado_ate is None


def test_conta_inativa_e_login_inexistente_tem_a_mesma_resposta(api, criar_docente):
    inativo = criar_docente(ativo=False)
    r1 = _entrar(api, inativo.usuario.email)
    r2 = _entrar(api, "ninguem@teste.com")
    assert r1.status_code == r2.status_code == 401
    assert r1.data["detail"] == r2.data["detail"]


def test_login_sem_campos_devolve_400(api):
    assert api.post(LOGIN, {}, format="json").status_code == 400


# ============================================================== sessao
def test_token_da_acesso_a_api(api, orientador):
    tokens = _entrar(api, orientador.usuario.email).data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    assert api.get("/api/tccs/").status_code == 200
    me = api.get(ME)
    assert me.status_code == 200
    assert me.data["email"] == orientador.usuario.email


def test_api_sem_token_devolve_401(api):
    assert api.get("/api/tccs/").status_code == 401
    assert api.get(ME).status_code == 401


def test_refresh_troca_o_token_e_logout_invalida(api, orientador):
    r1 = _entrar(api, orientador.usuario.email).data["refresh"]

    rotacao = api.post(REFRESH, {"refresh": r1}, format="json")
    assert rotacao.status_code == 200
    r2 = rotacao.data["refresh"]
    # o refresh antigo foi para a lista negra ao ser trocado
    assert api.post(REFRESH, {"refresh": r1}, format="json").status_code == 401

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {rotacao.data['access']}")
    assert api.post(LOGOUT, {"refresh": r2}, format="json").status_code == 204
    api.credentials()
    assert api.post(REFRESH, {"refresh": r2}, format="json").status_code == 401


def test_professor_tcc_aparece_no_me(api, orientador):
    orientador.professor_tcc = True
    orientador.save()
    tokens = _entrar(api, orientador.usuario.email).data
    assert tokens["usuario"]["professor_tcc"] is True


# =========================================================== politica
@pytest.mark.parametrize(
    "senha", ["semmaiuscula1!", "SemNumero!!", "SemEspecial123", "tudominusculo"]
)
def test_senha_fraca_e_recusada(senha):
    with pytest.raises(ValidationError):
        SenhaForteValidator().validate(senha)


def test_senha_forte_passa():
    SenhaForteValidator().validate("Forte#2026")
