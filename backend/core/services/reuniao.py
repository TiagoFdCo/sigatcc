"""C3b (7.3): reuniao de alinhamento entre aluno e orientador (RBN48, RD21).

- So existe depois do aceite da solicitacao (RD21).
- Aluno ou docente da solicitacao agenda; agendar de novo remarca a mesma
  reuniao (uma por solicitacao).
- Data futura; presencial com local descrito, remota com link valido.
- Conflito de agenda e ALERTADO, sem bloquear (criterio de aceite do 7.3): outra
  reuniao do aluno ou do docente, ou banca do docente, no mesmo intervalo.

A reuniao dura 1 h (DURACAO_REUNIAO), so para o calculo do conflito.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from core.models import (
    DURACAO_DEFESA,
    ParticipacaoBanca,
    ReuniaoAlinhamento,
    SolicitacaoOrientacao,
    StatusSolicitacao,
    TipoLocal,
)
from core.services.auditoria import registrar
from core.services.solicitacao import filtrar_visiveis

DURACAO_REUNIAO = timedelta(hours=1)
ENTIDADE = "REUNIAO_ALINHAMENTO"


def filtrar_reunioes_visiveis(usuario, queryset):
    """PF45: cada um ve as reunioes das solicitacoes que pode ver."""
    solicitacoes = filtrar_visiveis(usuario, SolicitacaoOrientacao.objects.all())
    return queryset.filter(solicitacao__in=solicitacoes.values("pk"))


def _validar_local(tipo_local, local):
    local = (local or "").strip()
    if not local:
        raise ValidationError({"local": "Informe o local ou o link da reunião."})
    if tipo_local == TipoLocal.REMOTO:
        try:
            URLValidator(schemes=["http", "https"])(local)
        except DjangoValidationError:
            raise ValidationError(
                {"local": "Reunião remota precisa de um link válido."}
            ) from None
    return local


def conflitos_de_agenda(solicitacao, data_hora):
    """Lista de alertas: reunioes do aluno ou do docente e bancas do docente que
    se sobrepoem ao intervalo [data_hora, data_hora + 1 h)."""
    inicio, fim = data_hora, data_hora + DURACAO_REUNIAO
    alertas = []

    outras = (
        ReuniaoAlinhamento.objects.exclude(solicitacao=solicitacao)
        .filter(
            data_hora__lt=fim,
            data_hora__gt=inicio - DURACAO_REUNIAO,
        )
        .select_related("solicitacao__aluno__usuario", "solicitacao__docente__usuario")
    )
    for r in outras.filter(solicitacao__docente=solicitacao.docente):
        alertas.append(
            f"O docente já tem reunião com {r.solicitacao.aluno.usuario.nome_completo}"
            f" às {timezone.localtime(r.data_hora):%d/%m %H:%M}."
        )
    for r in outras.filter(solicitacao__aluno=solicitacao.aluno):
        alertas.append(
            f"O aluno já tem reunião com {r.solicitacao.docente.usuario.nome_completo}"
            f" às {timezone.localtime(r.data_hora):%d/%m %H:%M}."
        )

    bancas = ParticipacaoBanca.objects.filter(
        usuario_id=solicitacao.docente_id,
        banca__data_hora_inicio__lt=fim,
        banca__data_hora_inicio__gt=inicio - DURACAO_DEFESA,
    ).select_related("banca__tcc")
    for p in bancas:
        alertas.append(
            f"O docente está na banca de “{p.banca.tcc.titulo}”"
            f" às {timezone.localtime(p.banca.data_hora_inicio):%d/%m %H:%M}."
        )
    return alertas


@transaction.atomic
def agendar_reuniao(*, solicitacao_id, usuario, data_hora, tipo_local, local):
    """PF44: agenda (ou remarca) a reuniao. Devolve (reuniao, criada, alertas)."""
    solicitacao = get_object_or_404(
        SolicitacaoOrientacao.objects.select_for_update().select_related(
            "aluno", "docente"
        ),
        pk=solicitacao_id,
    )
    if usuario.pk not in (solicitacao.aluno_id, solicitacao.docente_id):
        raise PermissionDenied("Só o aluno e o docente da solicitação agendam.")
    if solicitacao.status != StatusSolicitacao.ACEITA:
        raise ValidationError(
            {"solicitacao": "A reunião só pode ser agendada depois do aceite."}
        )
    if data_hora <= timezone.now():
        raise ValidationError({"data_hora": "A reunião deve ser em data futura."})
    local = _validar_local(tipo_local, local)

    novos = {"data_hora": data_hora, "tipo_local": tipo_local, "local": local}
    reuniao = ReuniaoAlinhamento.objects.filter(solicitacao=solicitacao).first()
    criada = reuniao is None
    if criada:
        reuniao = ReuniaoAlinhamento.objects.create(solicitacao=solicitacao, **novos)
        registrar(usuario, ENTIDADE, reuniao.id, "data_hora", None, data_hora)
    else:
        alterados = []
        for campo, valor in novos.items():
            anterior = getattr(reuniao, campo)
            if anterior != valor:
                registrar(usuario, ENTIDADE, reuniao.id, campo, anterior, valor)
                setattr(reuniao, campo, valor)
                alterados.append(campo)
        if alterados:
            reuniao.save(update_fields=alterados)
    return reuniao, criada, conflitos_de_agenda(solicitacao, data_hora)
