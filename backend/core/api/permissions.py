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


class SomenteAdministrador(BasePermission):
    """Consulta dos logs (C7, RNF08): so o administrador le LOG_AUDITORIA e LOG_ACESSO."""

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.tipo_usuario == TipoUsuario.ADMINISTRADOR
        )


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


class ProfessorTccOuAdministrador(BasePermission):
    """C16 (RBN58): o Professor de TCC cadastra membro externo na tela de banca."""

    message = "Só o Professor de TCC ou o administrador faz isto."

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        return usuario.tipo_usuario == TipoUsuario.ADMINISTRADOR or (
            escopo.eh_professor_tcc(usuario)
        )


class SomenteAluno(BasePermission):
    """Rotas "meu perfil" (C2a): so o proprio aluno logado."""

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.tipo_usuario == TipoUsuario.ALUNO
        )


class SemAluno(BasePermission):
    """Fecha a rota para o aluno: ele so ve o proprio TCC e o proprio perfil (C2a)."""

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.tipo_usuario != TipoUsuario.ALUNO
        )


class PainelDeGestao(BasePermission):
    """Dashboard de indicadores (C8): so docente, secretaria e administrador.

    Aluno e membro externo nao veem os indicadores agregados nem a carga de
    orientacao e de bancas de cada docente (RBN20-RBN23, RNF03).
    """

    PODEM_VER = {
        TipoUsuario.DOCENTE,
        TipoUsuario.SECRETARIA,
        TipoUsuario.ADMINISTRADOR,
    }

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.tipo_usuario in self.PODEM_VER
        )


class SomenteProfessorTCC(BasePermission):
    """Confirmacao do cadastro do aluno: so docente ativo marcado como Professor de TCC."""

    def has_permission(self, request, view):
        return _professor_tcc_ativo(request.user)


def _professor_tcc_ativo(usuario):
    if not (usuario and usuario.is_authenticated):
        return False
    if usuario.tipo_usuario != TipoUsuario.DOCENTE or not usuario.ativo:
        return False
    return escopo.eh_professor_tcc(usuario)
