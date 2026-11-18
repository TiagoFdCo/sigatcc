from datetime import datetime, timedelta
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import TCC, Aluno, Curso, Docente, Usuario, Banca, ParticipacaoBanca
from core.services.banca import validar_conflito_banca


@pytest.fixture
def cenario_banca(db):
    """Cria usuários, docente e TCC base."""
    user_docente1 = Usuario.objects.create_user(
        email="docente1_c4@uea.edu.br",
        nome_completo="Professor Avaliador 1",
        tipo_usuario="DOCENTE",
    )
    docente1 = Docente.objects.create(
        usuario=user_docente1,
        matricula_institucional="DOC401",
        departamento="EST",
    )

    user_aluno = Usuario.objects.create_user(
        email="aluno_c4@uea.edu.br",
        nome_completo="Aluno C4",
        tipo_usuario="ALUNO",
    )
    curso = Curso.objects.create(nome="Sistemas de Informação")
    aluno = Aluno.objects.create(usuario=user_aluno, matricula="ALU401", curso=curso)

    tcc = TCC.objects.create(
        titulo="TCC C4 Teste",
        autor=aluno,
        orientador=docente1,
        status="EM_DESENVOLVIMENTO",
    )

    return tcc, docente1, user_docente1


@pytest.mark.django_db
def test_conflito_membro_sobreposicao(cenario_banca):
    tcc, docente, user_docente = cenario_banca
    inicio_existente = timezone.now() + timedelta(days=5)

    # Cria banca 1 (das 14h às 16h no dia futuro)
    banca1 = Banca.objects.create(
        tcc=tcc,
        data_hora_inicio=inicio_existente,
        tipo_local="PRESENCIAL",
        bloco="A",
        sala="101",
    )
    ParticipacaoBanca.objects.create(banca=banca1, usuario=user_docente, tipo_membro="TITULAR")

    # Tenta criar banca 2 sobreposta (iniciando 1h depois com o mesmo docente)
    inicio_sobreposto = inicio_existente + timedelta(hours=1)
    with pytest.raises(ValidationError, match="Conflito de agenda"):
        validar_conflito_banca(
            data_hora_inicio=inicio_sobreposto,
            tipo_local="PRESENCIAL",
            bloco="B",
            sala="202",
            usuarios_membros_ids=[user_docente.id],
        )


@pytest.mark.django_db
def test_bancas_encostadas_sem_conflito(cenario_banca):
    tcc, docente, user_docente = cenario_banca
    inicio_existente = timezone.now() + timedelta(days=5)

    banca1 = Banca.objects.create(
        tcc=tcc,
        data_hora_inicio=inicio_existente,
        tipo_local="PRESENCIAL",
        bloco="A",
        sala="101",
    )
    ParticipacaoBanca.objects.create(banca=banca1, usuario=user_docente, tipo_membro="TITULAR")

    # Banca 2 inicia exatamente quando a Banca 1 termina (2 horas depois)
    inicio_encostado = inicio_existente + timedelta(hours=2)
    
    # Não deve levantar exceção!
    validar_conflito_banca(
        data_hora_inicio=inicio_encostado,
        tipo_local="PRESENCIAL",
        bloco="A",
        sala="101",
        usuarios_membros_ids=[user_docente.id],
    )
