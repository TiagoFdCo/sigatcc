"""B7a (cadastro e edicao de TCC)."""

from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from core.models import TCC, HistoricoStatus, StatusTCC
from core.services.auditoria import registrar

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
