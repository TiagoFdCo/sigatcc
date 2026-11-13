"""C16 (4.6): acesso temporario do membro externo da banca (RBN54, RBN58, RD32).

- O token nasce quando o externo ACEITA o convite de banca (PF35) e chega por
  e-mail. So o hash SHA-256 fica no banco (TOKEN_ACESSO.token_hash): quem le o
  banco nao consegue montar o link.
- Vale ate 48 h depois do horario registrado da defesa e expira sozinho.
- Com ele, o externo le o TCC e os dados da banca, sem login (RD34). O
  lancamento da avaliacao e do pacote 6.4 (D12).
- Cada acesso fica em LOG_ACESSO (quem e de qual IP).
"""

import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from core.models import LogAcesso, TokenAcesso
from core.services import email
from core.services.auditoria import registrar

VALIDADE_APOS_DEFESA = timedelta(hours=48)
ENTIDADE = "TOKEN_ACESSO"


def _hash(bruto):
    return hashlib.sha256(bruto.encode()).hexdigest()


def link_de_acesso(bruto):
    return email.link(f"/acesso-externo/{bruto}")


@transaction.atomic
def gerar_token(convite):
    """Cria (ou renova) o token do externo para a banca do convite aceito.

    Devolve (token, valor_bruto); o valor bruto so existe aqui e no e-mail.
    """
    externo = convite.usuario.membro_externo
    banca = convite.banca
    bruto = secrets.token_urlsafe(32)
    expira_em = banca.data_hora_inicio + VALIDADE_APOS_DEFESA
    token, _ = TokenAcesso.objects.update_or_create(
        membro_externo=externo,
        banca=banca,
        defaults={
            "token_hash": _hash(bruto),
            "expira_em": expira_em,
            "invalidado_em": None,
        },
    )
    registrar(convite.usuario, ENTIDADE, token.id, "expira_em", None, expira_em)

    tcc = banca.tcc
    validade = timezone.localtime(expira_em)
    email.enviar(
        para=[convite.usuario.email],
        assunto=f"Acesso ao TCC da banca: {tcc.titulo}",
        texto=(
            f"Olá, {convite.usuario.nome_completo}.\n\n"
            f"Obrigado por aceitar compor a banca do TCC “{tcc.titulo}”.\n\n"
            "Pelo link abaixo você lê o trabalho e vê os dados da defesa, sem "
            "precisar de senha:\n"
            f"{link_de_acesso(bruto)}\n\n"
            f"O link vale até {validade:%d/%m/%Y às %H:%M} (horário de Manaus), "
            "48 horas depois do início da defesa. Não compartilhe este e-mail."
        ),
    )
    return token, bruto


def validar_token(bruto):
    """Devolve o TOKEN_ACESSO valido ou levanta 404 (nao existe) ou 403."""
    token = (
        TokenAcesso.objects.select_related(
            "membro_externo__usuario",
            "banca__tcc__autor__usuario",
            "banca__tcc__orientador__usuario",
            "banca__tcc__coorientador__usuario",
            "banca__tcc__curso",
            "banca__tcc__area_conhecimento",
        )
        .filter(token_hash=_hash(bruto or ""))
        .first()
    )
    if token is None:
        raise NotFound("Link de acesso inválido.")
    if token.invalidado_em is not None:
        raise PermissionDenied("Este link de acesso foi cancelado.")
    if token.expira_em <= timezone.now():
        raise PermissionDenied(
            "Este link expirou: o acesso vale até 48 horas depois da defesa."
        )
    if not token.membro_externo.usuario.ativo:
        raise PermissionDenied("O acesso deste membro externo está desativado.")
    return token


def registrar_acesso(token, ip):
    LogAcesso.objects.create(usuario=token.membro_externo.usuario, ip=ip or "0.0.0.0")
