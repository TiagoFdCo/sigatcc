"""B5 (login e acesso): autenticacao com bloqueio por tentativas e LOG_ACESSO."""

from datetime import timedelta

from django.utils import timezone

from core.models import Docente, LogAcesso, Usuario

MAX_TENTATIVAS = 5  # RNF02 / RD26
TEMPO_BLOQUEIO = timedelta(minutes=15)


class CredenciaisInvalidas(Exception):
    """Login inexistente, conta inativa ou senha errada (mesma resposta para todos)."""


class ContaBloqueada(Exception):
    def __init__(self, ate):
        super().__init__(f"Conta bloqueada até {ate.isoformat()}")
        self.ate = ate


def buscar_usuario(login):
    """Aceita e-mail (qualquer perfil) ou matricula institucional (docente)."""
    login = (login or "").strip()
    if not login:
        return None
    if "@" in login:
        return Usuario.objects.filter(email__iexact=login).first()
    docente = (
        Docente.objects.select_related("usuario")
        .filter(matricula_institucional=login)
        .first()
    )
    return docente.usuario if docente else None


def autenticar(*, login, senha, ip):
    """Devolve o usuario autenticado ou levanta CredenciaisInvalidas/ContaBloqueada.

    Sem transacao de proposito: o contador de tentativas precisa ficar gravado
    mesmo quando a funcao termina com excecao.
    """
    usuario = buscar_usuario(login)
    if usuario is None or not usuario.ativo:
        raise CredenciaisInvalidas

    agora = timezone.now()
    if usuario.bloqueado_ate and usuario.bloqueado_ate > agora:
        raise ContaBloqueada(usuario.bloqueado_ate)

    if not usuario.check_password(senha):
        usuario.tentativas_falhas += 1
        bloqueou = usuario.tentativas_falhas >= MAX_TENTATIVAS
        if bloqueou:
            usuario.tentativas_falhas = 0
            usuario.bloqueado_ate = agora + TEMPO_BLOQUEIO
        usuario.save(update_fields=["tentativas_falhas", "bloqueado_ate"])
        if bloqueou:
            raise ContaBloqueada(usuario.bloqueado_ate)
        raise CredenciaisInvalidas

    usuario.tentativas_falhas = 0
    usuario.bloqueado_ate = None
    usuario.last_login = agora
    usuario.save(update_fields=["tentativas_falhas", "bloqueado_ate", "last_login"])
    LogAcesso.objects.create(usuario=usuario, ip=ip or "0.0.0.0")
    return usuario
