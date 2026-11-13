"""C16 (4.6): acesso temporario do membro externo (RBN54, RBN58, RD32; PF19, PF60).

Criterio de aceite do pacote: externo cadastrado na tela de banca; le o TCC no
prazo; o token expira sozinho.
"""

import re
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from core.models import Convite, LogAcesso, LogAuditoria, TokenAcesso, Usuario
from core.services import acesso_externo
from core.services import banca as servico_banca
from core.services import convites as servico_convites

pytestmark = pytest.mark.django_db


@pytest.fixture
def banca_com_externo(
    dados_banca,
    orientador,
    outros_docentes,
    membro_externo,
    django_capture_on_commit_callbacks,
):
    dados = {
        **dados_banca,
        "titulares": [
            orientador.usuario,
            membro_externo.usuario,
            outros_docentes[0].usuario,
        ],
    }
    with django_capture_on_commit_callbacks(execute=True):
        return servico_banca.cadastrar_banca(**dados, usuario=orientador.usuario)


@pytest.fixture
def convite_externo(banca_com_externo, membro_externo):
    return Convite.objects.get(banca=banca_com_externo, usuario=membro_externo.usuario)


def _aceitar(convite, capturar):
    mail.outbox.clear()
    with capturar(execute=True):
        servico_convites.responder_convite(convite_id=convite.pk, resposta="ACEITO")
    corpo = mail.outbox[-1].body
    return re.search(r"/acesso-externo/([\w-]+)", corpo).group(1)


# ------------------------------------------------------ token no aceite
def test_convite_do_externo_avisa_do_link_de_acesso(convite_externo, membro_externo):
    mensagem = next(m for m in mail.outbox if m.to == [membro_externo.usuario.email])
    assert "link de acesso ao TCC" in mensagem.body


def test_aceite_do_externo_gera_token_e_envia_o_link(
    convite_externo, banca_com_externo, django_capture_on_commit_callbacks
):
    bruto = _aceitar(convite_externo, django_capture_on_commit_callbacks)
    token = TokenAcesso.objects.get(banca=banca_com_externo)
    assert token.expira_em == banca_com_externo.data_hora_inicio + timedelta(hours=48)
    # so o hash fica no banco
    assert token.token_hash != bruto and len(token.token_hash) == 64
    assert LogAuditoria.objects.filter(
        entidade="TOKEN_ACESSO", registro_id=token.pk
    ).exists()


def test_recusa_do_externo_nao_gera_token(convite_externo):
    servico_convites.responder_convite(
        convite_id=convite_externo.pk, resposta="RECUSADO"
    )
    assert TokenAcesso.objects.count() == 0


def test_aceite_de_docente_nao_gera_token(banca_com_externo, outros_docentes):
    convite = Convite.objects.get(
        banca=banca_com_externo, usuario=outros_docentes[0].usuario
    )
    servico_convites.responder_convite(convite_id=convite.pk, resposta="ACEITO")
    assert TokenAcesso.objects.count() == 0


def test_externo_aceita_pelo_link_publico_e_recebe_o_acesso(
    api, convite_externo, django_capture_on_commit_callbacks
):
    c = servico_convites.assinatura(convite_externo)
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        resp = api.post(
            "/api/convites/link/", {"c": c, "resposta": "ACEITO"}, format="json"
        )
    assert resp.status_code == 200, resp.data
    assert resp.data["convidado_externo"] is True
    assert "/acesso-externo/" in mail.outbox[-1].body


# ------------------------------------------------- leitura pelo token
def test_token_le_o_tcc_sem_login_e_registra_o_acesso(
    api,
    convite_externo,
    banca_com_externo,
    membro_externo,
    django_capture_on_commit_callbacks,
):
    bruto = _aceitar(convite_externo, django_capture_on_commit_callbacks)
    resp = api.get(f"/api/acesso-externo/{bruto}/")
    assert resp.status_code == 200, resp.data
    assert resp.data["tcc"]["titulo"] == banca_com_externo.tcc.titulo
    assert resp.data["membro_nome"] == membro_externo.usuario.nome_completo
    assert len(resp.data["banca"]["membros"]) == 4
    assert any(m["membro_externo"] for m in resp.data["banca"]["membros"])
    assert LogAcesso.objects.filter(usuario=membro_externo.usuario).count() == 1


def test_token_inexistente_devolve_404(api):
    assert api.get("/api/acesso-externo/nao-existe/").status_code == 404


def test_token_expira_sozinho(api, convite_externo, django_capture_on_commit_callbacks):
    bruto = _aceitar(convite_externo, django_capture_on_commit_callbacks)
    TokenAcesso.objects.update(expira_em=timezone.now() - timedelta(minutes=1))
    resp = api.get(f"/api/acesso-externo/{bruto}/")
    assert resp.status_code == 403
    assert "expirou" in str(resp.data)


def test_token_cancelado_nao_abre(
    api, convite_externo, django_capture_on_commit_callbacks
):
    bruto = _aceitar(convite_externo, django_capture_on_commit_callbacks)
    TokenAcesso.objects.update(invalidado_em=timezone.now())
    assert api.get(f"/api/acesso-externo/{bruto}/").status_code == 403


def test_externo_desativado_nao_abre(
    api, convite_externo, membro_externo, django_capture_on_commit_callbacks
):
    bruto = _aceitar(convite_externo, django_capture_on_commit_callbacks)
    Usuario.objects.filter(pk=membro_externo.pk).update(ativo=False)
    assert api.get(f"/api/acesso-externo/{bruto}/").status_code == 403


def test_hash_e_estavel():
    assert acesso_externo._hash("abc") == acesso_externo._hash("abc")
    assert acesso_externo._hash("abc") != acesso_externo._hash("abd")


# --------------------------------------- cadastro do externo (PF60, RBN58)
CORPO_EXTERNO = {
    "nome_completo": "Profa. Convidada",
    "email": "convidada@ufam.edu.br",
    "instituicao_origem": "UFAM",
}


def test_professor_tcc_cadastra_membro_externo(api_como, professor_tcc):
    resp = api_como(professor_tcc.usuario).post(
        "/api/membros-externos/", CORPO_EXTERNO, format="json"
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["tipo_usuario"] == "MEMBRO_EXTERNO"
    assert resp.data["instituicao_origem"] == "UFAM"
    conta = Usuario.objects.get(email="convidada@ufam.edu.br")
    assert not conta.has_usable_password()  # entra so pelo token (RD34)


def test_administrador_tambem_cadastra(api_como, criar_usuario):
    resp = api_como(criar_usuario("ADMINISTRADOR")).post(
        "/api/membros-externos/", CORPO_EXTERNO, format="json"
    )
    assert resp.status_code == 201


def test_orientador_comum_nao_cadastra_externo(api_como, orientador):
    resp = api_como(orientador.usuario).post(
        "/api/membros-externos/", CORPO_EXTERNO, format="json"
    )
    assert resp.status_code == 403


def test_externo_sem_instituicao_e_recusado(api_como, professor_tcc):
    corpo = {k: v for k, v in CORPO_EXTERNO.items() if k != "instituicao_origem"}
    resp = api_como(professor_tcc.usuario).post(
        "/api/membros-externos/", corpo, format="json"
    )
    assert resp.status_code == 400
