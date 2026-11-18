import pytest
from django.core.exceptions import ValidationError

from core.services.publicacao import registrar_publicacao


@pytest.mark.django_db
def test_registrar_publicacao_apenas_com_link(tcc_em_andamento, usuario_orientador):
    dados = {
        "periodico": "Revista de Computação UEA",
        "issn_doi": "10.1234/sigatcc.2026",
        "data_publicacao": "2026-11-01",
        "link_artigo": "https://doi.org/10.1234/sigatcc.2026",
    }
    tcc = registrar_publicacao(tcc_em_andamento.pk, dados, usuario_orientador)
    assert tcc.status == "APROVADO_POR_PUBLICACAO"
    assert tcc.link_artigo == "https://doi.org/10.1234/sigatcc.2026"


@pytest.mark.django_db
def test_registrar_publicacao_sem_link_e_sem_comprovante_falha(tcc_em_andamento, usuario_orientador):
    dados = {
        "periodico": "Revista de Computação UEA",
        "issn_doi": "10.1234/sigatcc.2026",
        "data_publicacao": "2026-11-01",
    }
    with pytest.raises(ValidationError, match="link do artigo publicado ou anexar o arquivo"):
        registrar_publicacao(tcc_em_andamento.pk, dados, usuario_orientador)
