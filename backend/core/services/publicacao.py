"""C1 (aprovacao por publicacao): registra a publicacao e aprova o TCC."""

from django.core.exceptions import ValidationError as ErroDjango
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from core.models import TCC, Banca, ModalidadeConclusao, Publicacao, StatusTCC
from core.services import tcc as servico_tcc
from core.services.auditoria import registrar
from core.validators import validar_issn_doi

CAMPOS_OBRIGATORIOS = {
    "periodico": "Informe o periódico ou evento.",
    "issn_doi": "Informe o ISSN ou o DOI.",
    "data_publicacao": "Informe a data de publicação.",
    "comprovante_arquivo_path": "Informe o comprovante da publicação.",
}
CAMPOS_PUBLICACAO = (*CAMPOS_OBRIGATORIOS, "link_artigo")


def _limpar(dados):
    """Fica so com os campos da publicacao, sem espacos nas bordas, e exige os obrigatorios."""
    limpos = {}
    for campo in CAMPOS_PUBLICACAO:
        valor = dados.get(campo)
        limpos[campo] = valor.strip() if isinstance(valor, str) else valor
    for campo, mensagem in CAMPOS_OBRIGATORIOS.items():
        if not limpos[campo]:
            raise ValidationError({campo: mensagem})
    try:
        limpos["issn_doi"] = validar_issn_doi(limpos["issn_doi"])
    except ErroDjango as erro:
        raise ValidationError({"issn_doi": erro.messages[0]}) from erro
    limpos["link_artigo"] = limpos["link_artigo"] or None
    return limpos


def _validar_tcc(tcc):
    """RD07 e RD08: so TCC ativo, em desenvolvimento e na modalidade publicacao."""
    if not tcc.ativo:
        raise ValidationError({"tcc": "TCC inativo não recebe publicação."})
    if tcc.modalidade != ModalidadeConclusao.PUBLICACAO_APROVADA:
        raise ValidationError(
            {"tcc": "Só TCC na modalidade Publicação aprovada recebe publicação."}
        )
    if tcc.status != StatusTCC.EM_DESENVOLVIMENTO:
        raise ValidationError(
            {"tcc": "Só TCC em desenvolvimento pode ser aprovado por publicação."}
        )
    if Publicacao.objects.filter(tcc=tcc).exists():
        raise ValidationError({"tcc": "Este TCC já tem publicação registrada."})
    if Banca.objects.filter(tcc=tcc).exists():
        raise ValidationError(
            {
                "tcc": "TCC com banca cadastrada não recebe publicação (nunca pelas duas)."
            }
        )


@transaction.atomic
def registrar_publicacao(*, tcc_id, dados, usuario):
    """Grava a PUBLICACAO e muda o TCC para APROVADO_POR_PUBLICACAO, tudo ou nada.

    A mudanca de situacao passa por `mudar_situacao`, que grava o historico e o
    log do status. Se qualquer passo falhar, nada fica gravado (R10, R21).
    """
    tcc = get_object_or_404(TCC.objects.select_for_update(), pk=tcc_id)
    dados = _limpar(dados)
    _validar_tcc(tcc)
    if dados["data_publicacao"] > timezone.localdate():
        raise ValidationError(
            {"data_publicacao": "A data de publicação não pode ser futura."}
        )

    publicacao = Publicacao.objects.create(tcc=tcc, **dados)
    registrar(usuario, "PUBLICACAO", publicacao.id, "tcc", None, tcc)
    return servico_tcc.mudar_situacao(
        tcc_id=tcc.pk,
        status=StatusTCC.APROVADO_POR_PUBLICACAO,
        usuario=usuario,
        justificativa=f"Publicação registrada: {publicacao.periodico}",
    )
