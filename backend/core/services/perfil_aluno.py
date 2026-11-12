"""C2a (perfil do aluno): o aluno mantem as proprias areas de interesse."""

from django.db import transaction

from core.models import Aluno
from core.services.auditoria import registrar


@transaction.atomic
def atualizar_areas_interesse(*, aluno, areas, usuario):
    """Troca as areas de interesse do aluno e grava um log da mudanca.

    Areas repetidas contam uma vez. Se nada mudou, nao grava nada.
    """
    aluno = Aluno.objects.select_for_update().get(pk=aluno.pk)
    novas = {area.pk: area for area in areas}

    antes = sorted(str(pk) for pk in aluno.areas_interesse.values_list("pk", flat=True))
    depois = sorted(str(pk) for pk in novas)
    if antes == depois:
        return aluno

    aluno.areas_interesse.set(novas.values())
    registrar(
        usuario,
        "ALUNO",
        aluno.pk,
        "areas_interesse",
        ",".join(antes) or None,
        ",".join(depois) or None,
    )
    return aluno
