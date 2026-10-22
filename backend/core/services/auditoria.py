from django.db import models

from core.models import LogAuditoria


def _como_texto(valor):
    """LOG_AUDITORIA guarda texto: objetos viram o id, datas viram ISO."""
    if valor is None:
        return None
    if isinstance(valor, models.Model):
        return str(valor.pk)
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return str(valor)


def registrar(responsavel, entidade, registro_id, campo, anterior, novo):
    """Grava uma linha em LOG_AUDITORIA (tabela somente de acrescimo).

    Nao abre transacao propria: roda dentro da de quem chama. Se o INSERT
    falhar, a excecao sobe e a operacao inteira e desfeita (R10, R21).
    """
    LogAuditoria.objects.create(
        responsavel=responsavel,
        entidade=entidade,
        registro_id=registro_id,
        campo=campo,
        valor_anterior=_como_texto(anterior),
        valor_novo=_como_texto(novo),
    )
