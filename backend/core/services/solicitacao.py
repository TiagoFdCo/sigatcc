from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import SolicitacaoOrientacao, TCC, LogAuditoria

@transaction.atomic
def criar_solicitacao_orientacao(aluno, docente, mensagem=None):
    # 1. Valida se docente aceita orientações
    if not docente.aceita_orientacoes:
        raise ValidationError("Este docente não está aceitando novas orientações.")
    
    # 2. RD20 / RBN46: Só aluno sem TCC ativo pode solicitar
    tcc_ativo = TCC.objects.filter(aluno=aluno, status__in=['EM_ANDAMENTO', 'DEFENDIDO']).exists()
    if tcc_ativo:
        raise ValidationError("O aluno já possui um TCC ativo cadastrado.")
    
    # 3. Verifica se já existe solicitação pendente para o mesmo docente
    solicitacao_pendente = SolicitacaoOrientacao.objects.filter(
        aluno=aluno, docente=docente, status='PENDENTE'
    ).exists()
    if solicitacao_pendente:
        raise ValidationError("Já existe uma solicitação pendente para este orientador.")

    solicitacao = SolicitacaoOrientacao.objects.create(
        aluno=aluno,
        docente=docente,
        mensagem=mensagem,
        status='PENDENTE',
        enviada_em=timezone.now()
    )

    # 4. Grava em LOG_AUDITORIA (qualquer falha desfaz com transaction.atomic)
    LogAuditoria.objects.create(
        usuario=aluno.usuario,
        acao="CRIAR_SOLICITACAO_ORIENTACAO",
        detalhes=f"Solicitação {solicitacao.id} enviada para o docente {docente.id}"
    )

    return solicitacao


@transaction.atomic
def responder_solicitacao_orientacao(solicitacao, status_resposta, motivo_recusa=None):
    if solicitacao.status != 'PENDENTE':
        raise ValidationError("Esta solicitação já foi respondida anteriormente.")

    if status_resposta not in ['ACEITA', 'RECUSADA']:
        raise ValidationError("Status inválido.")

    solicitacao.status = status_resposta
    solicitacao.motivo_recusa = motivo_recusa if status_resposta == 'RECUSADA' else None
    solicitacao.respondida_em = timezone.now()
    solicitacao.save()

    # RBN47 / D7: Aceite vincula o cadastro do TCC
    if status_resposta == 'ACEITA':
        TCC.objects.create(
            aluno=solicitacao.aluno,
            orientador=solicitacao.docente,
            status='EM_ANDAMENTO'
        )

    LogAuditoria.objects.create(
        usuario=solicitacao.docente.usuario,
        acao="RESPONDER_SOLICITACAO_ORIENTACAO",
        detalhes=f"Solicitação {solicitacao.id} foi {status_resposta}."
    )

    return solicitacao
