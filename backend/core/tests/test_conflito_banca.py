from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import Banca, ParticipacaoBanca, TipoLocal
from core.services.banca import validar_conflito_banca


@pytest.fixture
def cenario_banca(tcc, orientador):
    """TCC base e o orientador dele (fixtures do conftest)."""
    return tcc, orientador, orientador.usuario


@pytest.mark.django_db
def test_conflito_membro_sobreposicao(cenario_banca):
    """Verifica bloqueio quando um mesmo membro tem bancas com horários sobrepostos."""
    tcc, _docente, user_docente = cenario_banca
    inicio_existente = timezone.now() + timedelta(days=5)

    # Cria banca 1 (das 14h às 16h)
    banca1 = Banca.objects.create(
        tcc=tcc,
        data_hora_inicio=inicio_existente,
        tipo_local=TipoLocal.PRESENCIAL,
        bloco="A",
        sala="101",
    )
    ParticipacaoBanca.objects.create(
        banca=banca1, usuario=user_docente, tipo_membro="TITULAR"
    )

    # Tenta validar banca 2 sobreposta (iniciando 1h depois com o mesmo docente)
    inicio_sobreposto = inicio_existente + timedelta(hours=1)
    with pytest.raises(ValidationError):
        validar_conflito_banca(
            data_hora_inicio=inicio_sobreposto,
            tipo_local=TipoLocal.PRESENCIAL,
            bloco="B",
            sala="202",
            usuarios_membros_ids=[user_docente.id],
        )


@pytest.mark.django_db
def test_conflito_local_presencial(cenario_banca):
    """Verifica bloqueio quando duas bancas compartilham a mesma sala e bloco no mesmo horário."""
    tcc, _docente, _user_docente = cenario_banca
    inicio_existente = timezone.now() + timedelta(days=5)

    Banca.objects.create(
        tcc=tcc,
        data_hora_inicio=inicio_existente,
        tipo_local=TipoLocal.PRESENCIAL,
        bloco="A",
        sala="101",
    )

    inicio_sobreposto = inicio_existente + timedelta(minutes=30)
    with pytest.raises(ValidationError):
        validar_conflito_banca(
            data_hora_inicio=inicio_sobreposto,
            tipo_local=TipoLocal.PRESENCIAL,
            bloco="A",
            sala="101",
        )


@pytest.mark.django_db
def test_bancas_encostadas_sem_conflito(cenario_banca):
    """Garante que bancas seguidas (ex: 14h-16h e 16h-18h) não gerem falso positivo de conflito."""
    tcc, _docente, user_docente = cenario_banca
    inicio_existente = timezone.now() + timedelta(days=5)

    banca1 = Banca.objects.create(
        tcc=tcc,
        data_hora_inicio=inicio_existente,
        tipo_local=TipoLocal.PRESENCIAL,
        bloco="A",
        sala="101",
    )
    ParticipacaoBanca.objects.create(
        banca=banca1, usuario=user_docente, tipo_membro="TITULAR"
    )

    # Banca 2 inicia exatamente quando a Banca 1 termina (2h depois)
    inicio_encostado = inicio_existente + timedelta(hours=2)

    # Não deve lançar exceção
    validar_conflito_banca(
        data_hora_inicio=inicio_encostado,
        tipo_local=TipoLocal.PRESENCIAL,
        bloco="A",
        sala="101",
        usuarios_membros_ids=[user_docente.id],
    )
