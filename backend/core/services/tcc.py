"""B7a (cadastro de TCC) e B7b (situacao do TCC)."""

from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from core.models import (
    TCC,
    Banca,
    HistoricoStatus,
    ModalidadeConclusao,
    MotivoNaoApresentacao,
    Publicacao,
    StatusTCC,
)
from core.services.auditoria import registrar

# Para onde cada status pode ir. Status fora do dicionario sao finais.
TRANSICOES = {
    StatusTCC.EM_DESENVOLVIMENTO: {
        StatusTCC.APRESENTADO,
        StatusTCC.NAO_APRESENTADO,
        StatusTCC.APROVADO_POR_PUBLICACAO,
    },
}

# Status que so fazem sentido para uma modalidade de conclusao.
MODALIDADE_EXIGIDA = {
    StatusTCC.APRESENTADO: ModalidadeConclusao.DEFESA_EM_BANCA,
    StatusTCC.APROVADO_POR_PUBLICACAO: ModalidadeConclusao.PUBLICACAO_APROVADA,
}

# Campos que o PATCH pode alterar. Autor, curso e status ficam de fora.
CAMPOS_EDITAVEIS = (
    "titulo",
    "subtitulo",
    "area_conhecimento",
    "modalidade",
    "visibilidade",
    "orientador",
    "coorientador",
)


def _exigir_docente_ativo(docente, papel):
    if not docente.usuario.ativo:
        raise ValidationError({papel: f"O {papel} está inativo."})


def _validar_orientacao(orientador, coorientador):
    """RD04: coorientador diferente do orientador; os dois ativos."""
    _exigir_docente_ativo(orientador, "orientador")
    if coorientador is not None:
        if coorientador == orientador:
            raise ValidationError(
                {"coorientador": "O coorientador deve ser diferente do orientador."}
            )
        _exigir_docente_ativo(coorientador, "coorientador")


@transaction.atomic
def cadastrar_tcc(*, dados, usuario):
    """Cria o TCC, a primeira linha de HISTORICO_STATUS e o log, tudo ou nada."""
    autor = dados["autor"]
    _validar_orientacao(dados["orientador"], dados.get("coorientador"))
    # RD05: um TCC ativo por aluno e curso (o banco tambem garante)
    if TCC.objects.filter(autor=autor, curso=autor.curso, ativo=True).exists():
        raise ValidationError({"autor": "O aluno já tem um TCC ativo neste curso."})

    tcc = TCC.objects.create(
        **dados, curso=autor.curso, status=StatusTCC.EM_DESENVOLVIMENTO
    )
    HistoricoStatus.objects.create(
        tcc=tcc, status=tcc.status, justificativa="Cadastro do TCC"
    )
    registrar(usuario, "TCC", tcc.id, "status", None, tcc.status)
    return tcc


@transaction.atomic
def atualizar_tcc(*, tcc_id, dados, usuario):
    """Edita os dados do TCC, com as mesmas regras do cadastro e um log por campo."""
    tcc = get_object_or_404(TCC.objects.select_for_update(), pk=tcc_id)
    if "autor" in dados and dados["autor"] != tcc.autor:
        raise ValidationError({"autor": "O autor do TCC não pode ser trocado."})
    if "orientador" in dados or "coorientador" in dados:
        _validar_orientacao(
            dados.get("orientador", tcc.orientador),
            dados.get("coorientador", tcc.coorientador),
        )
    # RD07 e RD08: banca e publicacao nunca coexistem; trocar de modalidade
    # com uma delas ja registrada abriria essa brecha (C1)
    if "modalidade" in dados and dados["modalidade"] != tcc.modalidade:
        if Publicacao.objects.filter(tcc=tcc).exists():
            raise ValidationError(
                {"modalidade": "TCC com publicação registrada não muda de modalidade."}
            )
        if Banca.objects.filter(tcc=tcc).exists():
            raise ValidationError(
                {"modalidade": "TCC com banca cadastrada não muda de modalidade."}
            )

    alterados = []
    for campo in CAMPOS_EDITAVEIS:
        if campo not in dados:
            continue
        anterior, novo = getattr(tcc, campo), dados[campo]
        if anterior == novo:
            continue
        setattr(tcc, campo, novo)
        alterados.append(campo)
        registrar(usuario, "TCC", tcc.id, campo, anterior, novo)
    if alterados:
        tcc.save(update_fields=alterados)
    return tcc


@transaction.atomic
def mudar_situacao(
    *,
    tcc_id,
    status,
    usuario,
    motivo_nao_apresentacao=None,
    motivo_outro=None,
    justificativa=None,
):
    """Muda o status do TCC se a transicao for permitida; grava historico e log."""
    tcc = get_object_or_404(TCC.objects.select_for_update(), pk=tcc_id)
    anterior = tcc.status

    if not tcc.ativo:
        raise ValidationError("TCC inativo não muda de situação.")
    if status not in TRANSICOES.get(anterior, set()):
        raise ValidationError(
            {"status": f"Transição {anterior} → {status} não permitida."}
        )
    exigida = MODALIDADE_EXIGIDA.get(status)
    if exigida and tcc.modalidade != exigida:
        raise ValidationError(
            {"status": f"{status} só vale para TCC na modalidade {exigida}."}
        )
    if (
        status == StatusTCC.APROVADO_POR_PUBLICACAO
        and not Publicacao.objects.filter(tcc=tcc).exists()
    ):  # C1: a aprovacao exige a publicacao registrada
        raise ValidationError(
            {
                "status": "Registre a publicação (periódico, ISSN/DOI, data e "
                "comprovante) para aprovar o TCC por publicação."
            }
        )
    if status == StatusTCC.NAO_APRESENTADO:  # RD11
        if not motivo_nao_apresentacao:
            raise ValidationError(
                {"motivo_nao_apresentacao": "Obrigatório para NAO_APRESENTADO."}
            )
        if motivo_nao_apresentacao == MotivoNaoApresentacao.OUTRO and not motivo_outro:
            raise ValidationError(
                {"motivo_outro": "Descreva o motivo quando for OUTRO."}
            )
        tcc.motivo_nao_apresentacao = motivo_nao_apresentacao
        tcc.motivo_outro = motivo_outro or None

    tcc.status = status
    tcc.save(update_fields=["status", "motivo_nao_apresentacao", "motivo_outro"])
    HistoricoStatus.objects.create(
        tcc=tcc,
        status=status,
        justificativa=justificativa or motivo_outro or motivo_nao_apresentacao,
    )
    registrar(usuario, "TCC", tcc.id, "status", anterior, status)
    return tcc
