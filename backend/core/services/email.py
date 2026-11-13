"""C5 (6.3): e-mail transacional (Resend por SMTP; RNF07).

Regras:
- O envio acontece DEPOIS do commit: se a operacao for desfeita, nenhum e-mail
  sai (transaction.on_commit).
- Falha no envio nao desfaz a operacao ja gravada: fica registrada no log da
  aplicacao, e o convite pode ser reenviado (PF33).
- O log nao guarda enderecos de e-mail (RNF12): so o assunto e a quantidade.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils.html import escape, urlize

logger = logging.getLogger("sigatcc.email")
PREFIXO_ASSUNTO = "[SIGATCC] "


def link(caminho):
    """Endereco absoluto de uma tela da SPA, para colocar no e-mail."""
    return f"{settings.SIGATCC_FRONTEND_URL}{caminho}"


def _html(texto):
    paragrafos = [p.strip() for p in texto.strip().split("\n\n") if p.strip()]
    corpo = "".join(
        f"<p>{urlize(escape(p)).replace(chr(10), '<br>')}</p>" for p in paragrafos
    )
    return (
        '<div style="font-family:Arial,sans-serif;font-size:15px;color:#1f2937">'
        f"{corpo}"
        '<p style="color:#6b7280;font-size:12px">SIGATCC · NUCOMP/UEA. '
        "Mensagem automática, não responda.</p></div>"
    )


def enviar_agora(*, para, assunto, texto):
    """Envia na hora. Devolve True se o servidor aceitou a mensagem."""
    mensagem = EmailMultiAlternatives(
        subject=f"{PREFIXO_ASSUNTO}{assunto}",
        body=texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=list(para),
    )
    mensagem.attach_alternative(_html(texto), "text/html")
    try:
        mensagem.send()
    except Exception:
        logger.exception(
            "Falha ao enviar o e-mail '%s' (%d destinatário(s))", assunto, len(para)
        )
        return False
    logger.info("E-mail '%s' enviado (%d destinatário(s))", assunto, len(para))
    return True


def enviar(*, para, assunto, texto):
    """Agenda o envio para depois do commit da transacao em andamento."""
    destinatarios = [e for e in para if e]
    if not destinatarios:
        return
    transaction.on_commit(
        lambda: enviar_agora(para=destinatarios, assunto=assunto, texto=texto)
    )
