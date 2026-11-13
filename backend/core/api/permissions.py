from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.models import TipoUsuario
from core.services import escopo


class LeituraOuGestao(BasePermission):
    """Leitura para qualquer usuario logado; escrita so para docente e administrador.

    O que cada perfil ve e edita em cada TCC fica em EscopoDoTCC (C17).
    """

    PODEM_ESCREVER = {TipoUsuario.DOCENTE, TipoUsuario.ADMINISTRADOR}

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return usuario.tipo_usuario in self.PODEM_ESCREVER


class LeituraOuAdministrador(BasePermission):
    """Leitura para qualquer usuario logado; escrita so para o administrador.

    Usada nos cadastros de pessoas (B6, B14): RBN57.
    """

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return usuario.tipo_usuario == TipoUsuario.ADMINISTRADOR


class GestaoDePessoas(BasePermission):
    """Cadastro de alunos e contas gerais (B14).

    Docente, secretaria e administrador consultam (precisam escolher autor e
    membros de banca); so o administrador escreve. Aluno e externo nao veem.
    """

    PODEM_LER = {
        TipoUsuario.DOCENTE,
        TipoUsuario.SECRETARIA,
        TipoUsuario.ADMINISTRADOR,
    }

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return usuario.tipo_usuario in self.PODEM_LER
        return usuario.tipo_usuario == TipoUsuario.ADMINISTRADOR


class EscopoDoTCC(BasePermission):
    """C17 (RBN56, RD29): o TCC pedido precisa estar no escopo do perfil.

    Leitura segue escopo.pode_ver_tcc; escrita, escopo.pode_editar_tcc. A
    recusa e registrada em LOG_AUDITORIA antes do 403.
    """

    message = "Você não tem acesso a este TCC."

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        if request.method in SAFE_METHODS:
            permitido = escopo.pode_ver_tcc(usuario, obj)
        else:
            permitido = escopo.pode_editar_tcc(usuario, obj)
        if not permitido:
            acao = f"{request.method} {getattr(view, 'action', '') or ''}".strip()
            escopo.registrar_acesso_negado(usuario, obj, acao)
        return permitido
