"""B8 (cadastro de banca: titulares, suplentes, data e local)."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import (
    TCC,
    Banca,
    Convite,
    ModalidadeConclusao,
    ParticipacaoBanca,
    StatusTCC,
    TipoConvite,
    TipoLocal,
    TipoMembroBanca,
    TipoUsuario,
)
from core.services.auditoria import registrar

TITULARES_POR_BANCA = 3
PODEM_COMPOR_BANCA = {TipoUsuario.DOCENTE, TipoUsuario.MEMBRO_EXTERNO}


def _validar_tcc(tcc):
    if not tcc.ativo or tcc.status != StatusTCC.EM_DESENVOLVIMENTO:
        raise ValidationError(
            {"tcc": "Só TCC ativo e em desenvolvimento recebe banca."}
        )
    if tcc.modalidade != ModalidadeConclusao.DEFESA_EM_BANCA:
        raise ValidationError({"tcc": "TCC aprovado por publicação não tem banca."})
    if Banca.objects.filter(tcc=tcc).exists():
        raise ValidationError({"tcc": "Este TCC já tem banca."})


def _validar_membros(tcc, titulares, suplentes):
    n = TITULARES_POR_BANCA
    if len(titulares) != n or len(set(titulares)) != n:
        raise ValidationError(
            {"titulares": f"Informe exatamente {n} titulares distintos."}
        )
    if tcc.orientador.usuario not in titulares:
        raise ValidationError({"titulares": "O orientador deve ser um dos titulares."})
    if len(set(suplentes)) != len(suplentes):
        raise ValidationError({"suplentes": "Há suplente repetido."})
    if set(titulares) & set(suplentes):
        raise ValidationError(
            {"suplentes": "Um membro não pode ser titular e suplente."}
        )
    for membro in [*titulares, *suplentes]:
        if membro.tipo_usuario not in PODEM_COMPOR_BANCA or not membro.ativo:
            raise ValidationError(
                {"membros": f"{membro.nome_completo} não pode compor banca."}
            )


def _validar_data_e_local(data_hora, tipo_local, local):
    if data_hora <= timezone.now():
        raise ValidationError({"data_hora": "A data da banca deve ser futura."})
    if not local:
        raise ValidationError({"local": "Informe a sala ou o link."})
    if tipo_local == TipoLocal.REMOTO:
        try:
            URLValidator(schemes=["http", "https"])(local)
        except DjangoValidationError:
            raise ValidationError(
                {"local": "Banca remota precisa de um link válido."}
            ) from None


@transaction.atomic
def cadastrar_banca(
    *, tcc, titulares, data_hora, tipo_local, local, usuario, suplentes=()
):
    """Grava BANCA, PARTICIPACAO_BANCA e os CONVITES pendentes, tudo ou nada.

    O envio dos convites (C5/C6) e o conflito de horario (C4) ficam para a E2.
    """
    tcc = TCC.objects.select_for_update().get(pk=tcc.pk)  # trava contra banca dupla
    titulares, suplentes = list(titulares), list(suplentes)
    local = (local or "").strip()

    _validar_tcc(tcc)
    _validar_membros(tcc, titulares, suplentes)
    _validar_data_e_local(data_hora, tipo_local, local)

    banca = Banca.objects.create(
        tcc=tcc, data_hora=data_hora, tipo_local=tipo_local, local=local
    )
    ParticipacaoBanca.objects.bulk_create(
        [
            ParticipacaoBanca(
                banca=banca, usuario=u, tipo_membro=TipoMembroBanca.TITULAR
            )
            for u in titulares
        ]
        + [
            ParticipacaoBanca(
                banca=banca, usuario=u, tipo_membro=TipoMembroBanca.SUPLENTE
            )
            for u in suplentes
        ]
    )
    Convite.objects.bulk_create(
        [
            Convite(banca=banca, usuario=u, tipo=TipoConvite.BANCA)
            for u in [*titulares, *suplentes]
            if u != tcc.orientador.usuario
        ]
    )
    registrar(usuario, "BANCA", banca.id, "data_hora", None, banca.data_hora)
    return banca
