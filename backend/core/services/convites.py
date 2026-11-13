"""C6 (6.3): convites de banca e de audiencia (RAN20, RBN49 a RBN51, RD22).

- O convite de banca nasce com a banca (B8) e sai por e-mail para cada membro,
  menos o orientador, que cadastrou a banca.
- O convite de audiencia e opcional e feito por pessoa (docente ou aluno).
- Todo convite leva o local (ou link) e o horario da defesa e um link para
  aceitar ou recusar. O link e assinado (django.core.signing): o membro
  externo responde sem login; quem tem login tambem responde pela tela.
- Responde-se uma vez, e so antes da defesa. Reenviar (PF33) so convite pendente.
- O aceite do membro externo gera o token de acesso temporario (C16).
"""

from django.core import signing
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from core.models import (
    Convite,
    ParticipacaoBanca,
    StatusConvite,
    TipoConvite,
    TipoLocal,
    TipoUsuario,
)
from core.services import acesso_externo, email
from core.services.auditoria import registrar
from core.services.escopo import pode_editar_tcc

SALT = "sigatcc.convite"
ENTIDADE = "CONVITE"
RESPOSTAS = {StatusConvite.ACEITO, StatusConvite.RECUSADO}
PODEM_ASSISTIR = {TipoUsuario.DOCENTE, TipoUsuario.ALUNO}
RELACIONADOS = (
    "usuario",
    "banca__tcc__autor__usuario",
    "banca__tcc__orientador__usuario",
)


# ------------------------------------------------------------------ link
def assinatura(convite):
    return signing.dumps(str(convite.pk), salt=SALT)


def link_resposta(convite):
    return email.link(f"/convites/responder?c={assinatura(convite)}")


def convite_por_assinatura(valor):
    try:
        pk = signing.loads(valor or "", salt=SALT)
    except signing.BadSignature:
        raise ValidationError({"c": "Link de convite inválido."}) from None
    return get_object_or_404(Convite.objects.select_related(*RELACIONADOS), pk=pk)


# --------------------------------------------------------------- e-mail
def descrever_local(banca):
    if banca.tipo_local == TipoLocal.REMOTO:
        return f"Remota: {banca.link_remoto}"
    return f"Presencial: bloco {banca.bloco}, sala {banca.sala}"


def papel_na_banca(convite):
    if convite.tipo == TipoConvite.AUDIENCIA:
        return None
    participacao = ParticipacaoBanca.objects.filter(
        banca_id=convite.banca_id, usuario_id=convite.usuario_id
    ).first()
    return participacao.tipo_membro if participacao else None


def _mensagem(convite):
    banca = convite.banca
    tcc = banca.tcc
    inicio = timezone.localtime(banca.data_hora_inicio)
    fim = timezone.localtime(banca.data_hora_fim)
    if convite.tipo == TipoConvite.AUDIENCIA:
        assunto = f"Convite para assistir à defesa: {tcc.titulo}"
        convite_para = "assistir à defesa"
    else:
        papel = "suplente" if papel_na_banca(convite) == "SUPLENTE" else "titular"
        assunto = f"Convite para banca: {tcc.titulo}"
        convite_para = f"compor a banca examinadora, como {papel},"
    texto = (
        f"Olá, {convite.usuario.nome_completo}.\n\n"
        f"Você foi convidado(a) para {convite_para} do TCC “{tcc.titulo}”, "
        f"de {tcc.autor.usuario.nome_completo}, orientado por "
        f"{tcc.orientador.usuario.nome_completo}.\n\n"
        f"Data: {inicio:%d/%m/%Y}, das {inicio:%H:%M} às {fim:%H:%M} "
        "(horário de Manaus)\n"
        f"Local: {descrever_local(banca)}\n\n"
        f"Para aceitar ou recusar, acesse:\n{link_resposta(convite)}"
    )
    if (
        convite.tipo == TipoConvite.BANCA
        and convite.usuario.tipo_usuario == TipoUsuario.MEMBRO_EXTERNO
    ):
        texto += (
            "\n\nAo aceitar, você recebe por e-mail o link de acesso ao TCC, "
            "válido até 48 horas depois do início da defesa."
        )
    return assunto, texto


def enviar_email_do_convite(convite):
    assunto, texto = _mensagem(convite)
    email.enviar(para=[convite.usuario.email], assunto=assunto, texto=texto)


def enviar_convites_da_banca(banca):
    """Chamado no cadastro da banca: um e-mail por convite."""
    for convite in banca.convites.select_related(*RELACIONADOS):
        enviar_email_do_convite(convite)


# ------------------------------------------------------------- regras
def _checar_defesa_futura(banca):
    if banca.data_hora_inicio <= timezone.now():
        raise ValidationError({"convite": "A defesa já começou ou já aconteceu."})


def _checar_editor(usuario, banca):
    if not pode_editar_tcc(usuario, banca.tcc):
        raise PermissionDenied("Só quem edita o TCC gerencia os convites da banca.")


def _travar(convite_id):
    return get_object_or_404(
        Convite.objects.select_for_update().select_related(*RELACIONADOS),
        pk=convite_id,
    )


@transaction.atomic
def reenviar_convite(*, convite_id, usuario):
    """PF33: reenvia um convite pendente e atualiza a data de envio (D16)."""
    convite = _travar(convite_id)
    _checar_editor(usuario, convite.banca)
    if convite.status != StatusConvite.PENDENTE:
        raise ValidationError({"convite": "Só convite pendente pode ser reenviado."})
    _checar_defesa_futura(convite.banca)
    anterior = convite.enviado_em
    convite.enviado_em = timezone.now()
    convite.save(update_fields=["enviado_em"])
    registrar(usuario, ENTIDADE, convite.id, "enviado_em", anterior, convite.enviado_em)
    enviar_email_do_convite(convite)
    return convite


@transaction.atomic
def convidar_audiencia(*, banca, usuarios, usuario):
    """PF34: um convite de audiencia por pessoa (docente ou aluno)."""
    _checar_editor(usuario, banca)
    _checar_defesa_futura(banca)
    usuarios = list(dict.fromkeys(usuarios))  # sem repetidos, na ordem
    if not usuarios:
        raise ValidationError({"usuarios": "Escolha pelo menos uma pessoa."})
    membros = set(banca.participacoes.values_list("usuario_id", flat=True))
    ja_convidados = set(banca.convites.values_list("usuario_id", flat=True))
    for pessoa in usuarios:
        if pessoa.tipo_usuario not in PODEM_ASSISTIR or not pessoa.ativo:
            raise ValidationError(
                {"usuarios": f"{pessoa.nome_completo} não pode ser convidado(a)."}
            )
        if pessoa.pk in membros or pessoa.pk == banca.tcc.autor_id:
            raise ValidationError(
                {"usuarios": f"{pessoa.nome_completo} já participa da defesa."}
            )
        if pessoa.pk in ja_convidados:
            raise ValidationError(
                {"usuarios": f"{pessoa.nome_completo} já foi convidado(a)."}
            )
    criados = []
    for pessoa in usuarios:
        convite = Convite.objects.create(
            banca=banca, usuario=pessoa, tipo=TipoConvite.AUDIENCIA
        )
        registrar(usuario, ENTIDADE, convite.id, "status", None, convite.status)
        enviar_email_do_convite(convite)
        criados.append(convite)
    return criados


@transaction.atomic
def responder_convite(*, convite_id, resposta):
    """PF35: o convidado aceita ou recusa, uma vez, antes da defesa."""
    convite = _travar(convite_id)
    if convite.status != StatusConvite.PENDENTE:
        raise ValidationError({"resposta": "Este convite já foi respondido."})
    if resposta not in RESPOSTAS:
        raise ValidationError({"resposta": "Responda com ACEITO ou RECUSADO."})
    _checar_defesa_futura(convite.banca)
    convite.status = resposta
    convite.respondido_em = timezone.now()
    convite.save(update_fields=["status", "respondido_em"])
    registrar(
        convite.usuario,
        ENTIDADE,
        convite.id,
        "status",
        StatusConvite.PENDENTE,
        resposta,
    )
    # C16 (RBN54, RD32): o aceite do externo gera o token de acesso ao TCC
    if (
        resposta == StatusConvite.ACEITO
        and convite.tipo == TipoConvite.BANCA
        and convite.usuario.tipo_usuario == TipoUsuario.MEMBRO_EXTERNO
    ):
        acesso_externo.gerar_token(convite)
    return convite


def responder_como_usuario(*, convite_id, resposta, usuario):
    """Resposta pela tela, de quem tem login: so o proprio convidado."""
    convite = get_object_or_404(Convite, pk=convite_id)
    if convite.usuario_id != usuario.pk:
        raise PermissionDenied("Só o convidado responde ao convite.")
    return responder_convite(convite_id=convite.pk, resposta=resposta)


def responder_por_link(*, valor_assinatura, resposta):
    """Resposta pelo link do e-mail (sem login; usada pelo membro externo)."""
    convite = convite_por_assinatura(valor_assinatura)
    return responder_convite(convite_id=convite.pk, resposta=resposta)
