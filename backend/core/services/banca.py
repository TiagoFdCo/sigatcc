"""B8 (cadastro de banca: titulares, suplentes, data e local) e C4 (validação de conflitos)."""

from datetime import timedelta

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
from core.services import convites as servico_convites
from core.services.auditoria import registrar

TITULARES_POR_BANCA = 3
PODEM_COMPOR_BANCA = {TipoUsuario.DOCENTE, TipoUsuario.MEMBRO_EXTERNO}


def validar_conflito_banca(
    data_hora_inicio,
    tipo_local,
    bloco=None,
    sala=None,
    link_remoto=None,
    usuarios_membros_ids=None,
    banca_id_atual=None,
):
    """C4 (RBN13, RD16, RNF04): Valida sobreposição de horário por membro ou local.

    Regra: Dois intervalos [inicio, inicio + 2h) que se sobrepõem geram conflito
    se compartilharem o mesmo membro (docente ou externo) ou o mesmo local (presencial ou remoto).
    Bancas encostadas (ex: 14h-16h e 16h-18h) são permitidas.
    """
    inicio_novo = data_hora_inicio
    fim_novo = inicio_novo + timedelta(hours=2)

    # So busca as bancas que podem se sobrepor, as que comecam entre
    # (inicio - 2 h) e o fim da nova, em vez de varrer todas (RNF04, CT-BAN-04).
    bancas_existentes = Banca.objects.filter(
        data_hora_inicio__gt=inicio_novo - timedelta(hours=2),
        data_hora_inicio__lt=fim_novo,
    )
    if banca_id_atual:
        bancas_existentes = bancas_existentes.exclude(pk=banca_id_atual)

    for banca in bancas_existentes:
        inicio_existente = banca.data_hora_inicio
        fim_existente = inicio_existente + timedelta(hours=2)

        # Checa sobreposição temporal rigorosa [inicio, fim)
        se_sobrepoe = (inicio_existente < fim_novo) and (fim_existente > inicio_novo)

        if se_sobrepoe:
            # 1. Conflito de Local
            if (
                tipo_local == TipoLocal.PRESENCIAL
                and banca.tipo_local == TipoLocal.PRESENCIAL
                and banca.bloco == bloco
                and banca.sala == sala
            ):
                raise ValidationError(
                    {
                        "local": f"Conflito de local: a sala {sala} do bloco {bloco} já está reservada para outra banca nesse horário."
                    }
                )
            elif (
                tipo_local == TipoLocal.REMOTO
                and banca.tipo_local == TipoLocal.REMOTO
                and banca.link_remoto
                and link_remoto
                and banca.link_remoto == link_remoto
            ):
                raise ValidationError(
                    {
                        "link_remoto": "Conflito de local remoto: este link de reunião já está em uso por outra banca nesse horário."
                    }
                )

            # 2. Conflito de Membro (Docente / Membro Externo)
            if usuarios_membros_ids:
                membros_existentes = ParticipacaoBanca.objects.filter(
                    banca=banca,
                    usuario_id__in=usuarios_membros_ids,
                ).select_related("usuario")

                if membros_existentes.exists():
                    nome_membro = membros_existentes.first().usuario.nome_completo
                    raise ValidationError(
                        {
                            "membros": f"Conflito de agenda: O(a) avaliador(a) {nome_membro} já possui banca agendada nesse horário."
                        }
                    )


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


def _texto(valor):
    return (valor or "").strip() or None


def _validar_data(data_hora_inicio):
    if data_hora_inicio <= timezone.now():
        raise ValidationError({"data_hora_inicio": "A data da banca deve ser futura."})


def _local(tipo_local, bloco, sala, link_remoto):
    """D17 / RBN12: presencial exige bloco e sala; remota, um link valido."""
    bloco, sala, link_remoto = _texto(bloco), _texto(sala), _texto(link_remoto)
    if tipo_local == TipoLocal.REMOTO:
        try:
            URLValidator(schemes=["http", "https"])(link_remoto or "")
        except DjangoValidationError:
            raise ValidationError(
                {"link_remoto": "Banca remota precisa de um link válido."}
            ) from None
        return {"bloco": None, "sala": None, "link_remoto": link_remoto}
    if not bloco:
        raise ValidationError({"bloco": "Informe o bloco da defesa presencial."})
    if not sala:
        raise ValidationError({"sala": "Informe a sala da defesa presencial."})
    return {"bloco": bloco, "sala": sala, "link_remoto": None}


@transaction.atomic
def cadastrar_banca(
    *,
    tcc,
    titulares,
    data_hora_inicio,
    tipo_local,
    usuario,
    suplentes=(),
    bloco=None,
    sala=None,
    link_remoto=None,
):
    """Grava BANCA, PARTICIPACAO_BANCA e os CONVITES pendentes, tudo ou nada.

    A defesa dura 2 h (D5): só o início é guardado. Valida conflito de horário e local (C4).
    """
    tcc = TCC.objects.select_for_update().get(pk=tcc.pk)  # trava contra banca dupla
    titulares, suplentes = list(titulares), list(suplentes)

    _validar_tcc(tcc)
    _validar_membros(tcc, titulares, suplentes)
    _validar_data(data_hora_inicio)
    local = _local(tipo_local, bloco, sala, link_remoto)

    # C4: Validação de conflito de horário e de local antes de salvar
    todos_membros_ids = [m.id for m in [*titulares, *suplentes]]
    validar_conflito_banca(
        data_hora_inicio=data_hora_inicio,
        tipo_local=tipo_local,
        bloco=local.get("bloco"),
        sala=local.get("sala"),
        link_remoto=local.get("link_remoto"),
        usuarios_membros_ids=todos_membros_ids,
    )

    banca = Banca.objects.create(
        tcc=tcc, data_hora_inicio=data_hora_inicio, tipo_local=tipo_local, **local
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
    registrar(
        usuario, "BANCA", banca.id, "data_hora_inicio", None, banca.data_hora_inicio
    )
    # C6: os convites saem por e-mail depois do commit (RBN49, RBN51)
    servico_convites.enviar_convites_da_banca(banca)
    return banca
