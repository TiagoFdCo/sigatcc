import pytest
from django.core.exceptions import ValidationError

from core.models import TCC, Aluno, Curso, Docente, Usuario
from core.services.publicacao import registrar_publicacao


@pytest.fixture
def cenario_publicacao(db):
    """Cria a estrutura completa de relacionamentos necessária para o TCC."""
    user_orientador = Usuario.objects.create_user(
        email="orientador_c1@uea.edu.br",
        nome_completo="Professor Orientador C1",
        tipo_usuario="DOCENTE",
    )
    docente = Docente.objects.create(
        usuario=user_orientador,
        matricula_institucional="DOC123456",
        departamento="DCC",
    )

    user_aluno = Usuario.objects.create_user(
        email="aluno_c1@uea.edu.br",
        nome_completo="Aluno C1",
        tipo_usuario="ALUNO",
    )
    curso = Curso.objects.create(nome="Licenciatura em Computação")
    aluno = Aluno.objects.create(
        usuario=user_aluno,
        matricula="ALU123456",
        curso=curso,
    )

    tcc = TCC.objects.create(
        titulo="Trabalho de Conclusão C1",
        autor=aluno,
        orientador=docente,
        status="EM_DESENVOLVIMENTO",
    )

    return tcc, user_orientador


@pytest.mark.django_db
def test_registrar_publicacao_apenas_com_link(cenario_publicacao):
    tcc, orientador = cenario_publicacao
    dados = {
        "periodico": "Revista de Computação UEA",
        "issn_doi": "10.1234/sigatcc.2026",
        "data_publicacao": "2026-11-01",
        "link_artigo": "https://doi.org/10.1234/sigatcc.2026",
    }
    tcc_atualizado = registrar_publicacao(tcc.pk, dados, orientador)
    assert tcc_atualizado.status == "APROVADO_POR_PUBLICACAO"
    assert tcc_atualizado.link_artigo == "https://doi.org/10.1234/sigatcc.2026"


@pytest.mark.django_db
def test_registrar_publicacao_sem_link_e_sem_comprovante_falha(cenario_publicacao):
    tcc, orientador = cenario_publicacao
    dados = {
        "periodico": "Revista de Computação UEA",
        "issn_doi": "10.1234/sigatcc.2026",
        "data_publicacao": "2026-11-01",
    }
    with pytest.raises(ValidationError, match="link do artigo publicado ou anexar o arquivo"):
        registrar_publicacao(tcc.pk, dados, orientador)
