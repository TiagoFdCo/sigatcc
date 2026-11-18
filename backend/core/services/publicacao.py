from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import TCC, LogAuditoria


def registrar_publicacao(tcc_id, dados, usuario):
    """C1: Registra a publicação científica do TCC e altera a situação para APROVADO_POR_PUBLICACAO.
    
    Regra (DER v2 / Pacote 5.3): É obrigatório fornecer o link do artigo OU o arquivo do comprovante (RBN34/RD08).
    """
    link_artigo = dados.get("link_artigo")
    comprovante_arquivo = dados.get("comprovante_arquivo")

    # Validação da regra "link OU comprovante"
    if not link_artigo and not comprovante_arquivo:
        raise ValidationError(
            "É necessário fornecer o link do artigo publicado ou anexar o arquivo do comprovante."
        )

    # Validação de tamanho máximo do arquivo PDF (máx. 5 MB)
    if comprovante_arquivo:
        if comprovante_arquivo.size > 5 * 1024 * 1024:
            raise ValidationError("O arquivo do comprovante não pode exceder 5 MB.")
        if not comprovante_arquivo.name.lower().endswith(".pdf"):
            raise ValidationError("O comprovante deve ser um arquivo PDF.")

    with transaction.atomic():
        tcc = TCC.objects.select_for_update().get(pk=tcc_id)
        
        tcc.periodico = dados.get("periodico")
        tcc.issn_doi = dados.get("issn_doi")
        tcc.data_publicacao = dados.get("data_publicacao")
        
        if link_artigo:
            tcc.link_artigo = link_artigo
        if comprovante_arquivo:
            tcc.comprovante_arquivo_path = comprovante_arquivo.name

        tcc.status = "APROVADO_POR_PUBLICACAO"
        tcc.save()

        LogAuditoria.objects.create(
            entidade="TCC",
            registro_id=tcc.pk,
            campo="status",
            valor_antigo=tcc.status,
            valor_novo="APROVADO_POR_PUBLICACAO",
            responsavel=usuario,
        )

        return tcc
