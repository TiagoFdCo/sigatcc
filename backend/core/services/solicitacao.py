"""C3a (7.2): solicitacao e aceite de orientacao (RAN19, RBN46, RBN47, RD20).

- O aluno so solicita se nao tem TCC ativo e se nao tem orientacao ja aceita.
- So docente ativo e que aceita orientacoes recebe solicitacao.
- O docente responde uma unica vez; o motivo da recusa e opcional (D15).
- O aceite libera o cadastro do TCC com esse docente como orientador: quem
  cadastra o TCC continua sendo o orientador (ou o Professor de TCC), pelo fluxo
  de /api/tccs/; a tela abre o cadastro ja com o aluno preenchido.

Toda escrita grava LOG_AUDITORIA na mesma transacao (falha no log desfaz tudo).
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from core.models import TCC, SolicitacaoOrientacao, StatusSolicitacao, TipoUsuario
from core.services.auditoria import registrar
from core.services.escopo import eh_professor_tcc

ENTIDADE = "SOLICITACAO_ORIENTACAO"
RESPOSTAS = {StatusSolicitacao.ACEITA, StatusSolicitacao.RECUSADA}


def aluno_tem_tcc_ativo(aluno):
    """TCC ativo no mesmo sentido da carga de orientacao (RD17): ativo=True."""
    return TCC.objects.filter(autor=aluno, ativo=True).exists()


def filtrar_visiveis(usuario, queryset):
    """PF43: o aluno ve as que enviou; o docente, as que recebeu; Professor de
    TCC, Secretaria e administrador veem todas (RNF03)."""
    tipo = getattr(usuario, "tipo_usuario", None)
    if tipo in (TipoUsuario.ADMINISTRADOR, TipoUsuario.SECRETARIA):
        return queryset
    if tipo == TipoUsuario.DOCENTE:
        if eh_professor_tcc(usuario):
            return queryset
        return queryset.filter(docente_id=usuario.pk)
    if tipo == TipoUsuario.ALUNO:
        return queryset.filter(aluno_id=usuario.pk)
    return queryset.none()


def _texto(valor):
    return (valor or "").strip() or None


@transaction.atomic
def enviar_solicitacao(*, aluno, docente, mensagem=None, usuario):
    """PF41: o aluno envia a solicitacao a um docente."""
    if not docente.usuario.ativo or not docente.aceita_orientacoes:
        raise ValidationError(
            {"docente": "Este docente não está aceitando novas orientações."}
        )
    if aluno_tem_tcc_ativo(aluno):
        raise ValidationError(
            {"aluno": "Você já tem um TCC ativo e não pode solicitar orientação."}
        )
    minhas = SolicitacaoOrientacao.objects.select_for_update().filter(aluno=aluno)
    if minhas.filter(status=StatusSolicitacao.ACEITA).exists():
        raise ValidationError(
            {"aluno": "Você já tem uma orientação aceita. Aguarde o cadastro do TCC."}
        )
    if minhas.filter(docente=docente, status=StatusSolicitacao.PENDENTE).exists():
        raise ValidationError(
            {"docente": "Já existe uma solicitação pendente para este docente."}
        )

    solicitacao = SolicitacaoOrientacao.objects.create(
        aluno=aluno, docente=docente, mensagem=_texto(mensagem)
    )
    registrar(usuario, ENTIDADE, solicitacao.id, "status", None, solicitacao.status)
    return solicitacao


@transaction.atomic
def responder_solicitacao(*, solicitacao_id, status, usuario, motivo_recusa=None):
    """PF42: o docente da solicitacao aceita ou recusa, uma unica vez."""
    solicitacao = get_object_or_404(
        SolicitacaoOrientacao.objects.select_for_update(), pk=solicitacao_id
    )
    if solicitacao.docente_id != usuario.pk:
        raise PermissionDenied("Só o docente procurado responde a solicitação.")
    if solicitacao.status != StatusSolicitacao.PENDENTE:
        raise ValidationError({"status": "Esta solicitação já foi respondida."})
    if status not in RESPOSTAS:
        raise ValidationError({"status": "Responda com ACEITA ou RECUSADA."})
    if status == StatusSolicitacao.ACEITA and aluno_tem_tcc_ativo(solicitacao.aluno):
        raise ValidationError(
            {
                "status": "O aluno já tem um TCC ativo; a solicitação não pode ser aceita."
            }
        )

    anterior = solicitacao.status
    solicitacao.status = status
    solicitacao.motivo_recusa = (
        _texto(motivo_recusa) if status == StatusSolicitacao.RECUSADA else None
    )
    solicitacao.respondida_em = timezone.now()
    solicitacao.save(update_fields=["status", "motivo_recusa", "respondida_em"])
    registrar(usuario, ENTIDADE, solicitacao.id, "status", anterior, status)
    return solicitacao
