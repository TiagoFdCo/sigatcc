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
