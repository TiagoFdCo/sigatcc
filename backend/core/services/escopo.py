"""C17 (4.7): visao por perfil. Quem ve e quem edita cada TCC (RBN56, RD29, RNF03).

- Administrador e Secretaria veem todos os TCCs (a Secretaria so le: RBN55).
- Professor de TCC (docente com professor_tcc) ve e edita todos.
- Orientador ve e edita so os TCCs em que e orientador ou coorientador.
- Aluno ve so o proprio TCC (RD24) e nao edita.
- Membro externo nao lista TCCs: o acesso dele e pelo token da banca (4.6, E3).

Tentativa de abrir ou editar um TCC fora do escopo e recusada e registrada em
LOG_AUDITORIA (campo "acesso_negado").
"""

from django.db.models import Q

from core.models import TipoUsuario
from core.services.auditoria import registrar

VEEM_TODOS = {TipoUsuario.ADMINISTRADOR, TipoUsuario.SECRETARIA}


def eh_professor_tcc(usuario):
    docente = getattr(usuario, "docente", None)
    return bool(docente and docente.professor_tcc)


def _orienta(usuario, tcc):
    return usuario.pk in (tcc.orientador_id, tcc.coorientador_id)


def filtrar_tccs_visiveis(usuario, queryset):
    """Restringe uma consulta de TCC ao que o usuario pode ver."""
    tipo = getattr(usuario, "tipo_usuario", None)  # anonimo: nenhum escopo
    if tipo in VEEM_TODOS:
        return queryset
    if tipo == TipoUsuario.DOCENTE:
        if eh_professor_tcc(usuario):
            return queryset
        # DOCENTE.pk e ALUNO.pk sao o id do usuario
        return queryset.filter(
            Q(orientador_id=usuario.pk) | Q(coorientador_id=usuario.pk)
        )
    if tipo == TipoUsuario.ALUNO:
        return queryset.filter(autor_id=usuario.pk)
    return queryset.none()


def pode_ver_tcc(usuario, tcc):
    tipo = getattr(usuario, "tipo_usuario", None)  # anonimo: nenhum escopo
    if tipo in VEEM_TODOS:
        return True
    if tipo == TipoUsuario.DOCENTE:
        return eh_professor_tcc(usuario) or _orienta(usuario, tcc)
    if tipo == TipoUsuario.ALUNO:
        return tcc.autor_id == usuario.pk
    return False


def pode_editar_tcc(usuario, tcc):
    tipo = getattr(usuario, "tipo_usuario", None)  # anonimo: nenhum escopo
    if tipo == TipoUsuario.ADMINISTRADOR:
        return True
    if tipo == TipoUsuario.DOCENTE:
        return eh_professor_tcc(usuario) or _orienta(usuario, tcc)
    return False


def pode_cadastrar_tcc_para(usuario, orientador):
    """RD24: o TCC e cadastrado pelo proprio orientador ou pelo Professor de TCC."""
    tipo = getattr(usuario, "tipo_usuario", None)  # anonimo: nenhum escopo
    if tipo == TipoUsuario.ADMINISTRADOR:
        return True
    if tipo == TipoUsuario.DOCENTE:
        return eh_professor_tcc(usuario) or orientador.pk == usuario.pk
    return False


def registrar_acesso_negado(usuario, tcc, acao):
    """Grava a tentativa fora do escopo (criterio de aceite do pacote 4.7)."""
    registrar(usuario, "TCC", tcc.pk, "acesso_negado", None, acao)
