from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.models import TipoUsuario


class LeituraOuGestao(BasePermission):
    """Leitura para qualquer usuario logado; escrita so para docente e administrador.

    A visao por perfil (cada um ve so o que lhe cabe) e o item C15, na E2.
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
