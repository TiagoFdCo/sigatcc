"""C5 (6.3): e-mail transacional (Resend por SMTP; RNF07)."""

import logging

import pytest
from django.core import mail
from django.core.management import CommandError, call_command
from django.db import transaction

from core.services import email

pytestmark = pytest.mark.django_db


def test_envio_acontece_depois_do_commit(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        email.enviar(para=["a@exemplo.com"], assunto="Oi", texto="Olá\n\nTudo bem?")
        assert mail.outbox == []  # ainda dentro da transacao
    assert len(mail.outbox) == 1
    enviado = mail.outbox[0]
    assert enviado.subject == "[SIGATCC] Oi"
    assert enviado.to == ["a@exemplo.com"]
    html, tipo = enviado.alternatives[0]
    assert tipo == "text/html" and "<p>Tudo bem?</p>" in html


def test_rollback_nao_envia(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        try:
            with transaction.atomic():
                email.enviar(para=["a@exemplo.com"], assunto="Oi", texto="x")
                raise RuntimeError("desfaz")
        except RuntimeError:
            pass
    assert callbacks == [] and mail.outbox == []


def test_sem_destinatario_nao_agenda(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks() as callbacks:
        email.enviar(para=["", None], assunto="Oi", texto="x")
    assert callbacks == []


def test_link_usa_o_endereco_da_spa(settings):
    settings.SIGATCC_FRONTEND_URL = "https://homolog.sigatcc.com.br"
    assert email.link("/convites") == "https://homolog.sigatcc.com.br/convites"


def test_html_escapa_e_transforma_links():
    html = email._html("<b>x</b>\n\nAcesse https://exemplo.com/a")
    assert "&lt;b&gt;" in html
    assert '<a href="https://exemplo.com/a"' in html


def test_falha_no_envio_nao_quebra_e_nao_loga_endereco(monkeypatch, caplog):
    def falhar(self, fail_silently=False):
        raise OSError("SMTP fora do ar")

    monkeypatch.setattr("django.core.mail.EmailMultiAlternatives.send", falhar)
    with caplog.at_level(logging.ERROR, logger="sigatcc.email"):
        ok = email.enviar_agora(para=["segredo@exemplo.com"], assunto="Oi", texto="x")
    assert ok is False
    assert "Falha ao enviar" in caplog.text
    assert "segredo@exemplo.com" not in caplog.text


def test_comando_de_teste_envia_a_quantidade_pedida():
    call_command("enviar_email_teste", para="eu@exemplo.com", quantidade=3)
    assert len(mail.outbox) == 3


def test_comando_de_teste_recusa_quantidade_zero():
    with pytest.raises(CommandError):
        call_command("enviar_email_teste", para="eu@exemplo.com", quantidade=0)
