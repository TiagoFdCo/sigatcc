"""Fixtures compartilhadas pelos testes de TCC (B7) e banca (B8)."""

import itertools
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import (
    Aluno,
    AreaConhecimento,
    Curso,
    Docente,
    MembroExterno,
    TipoUsuario,
    Usuario,
)
from core.services import tcc as servico_tcc

_seq = itertools.count(1)


@pytest.fixture
def criar_usuario(db):
    def _criar(tipo=TipoUsuario.ALUNO, ativo=True):
        n = next(_seq)
        return Usuario.objects.create_user(
            f"pessoa{n}@teste.com",
            "senha-forte-123",
            nome_completo=f"Pessoa {n}",
            tipo_usuario=tipo,
            ativo=ativo,
        )

    return _criar


@pytest.fixture
def criar_docente(criar_usuario):
    def _criar(ativo=True):
        n = next(_seq)
        return Docente.objects.create(
            usuario=criar_usuario(TipoUsuario.DOCENTE, ativo=ativo),
            matricula_institucional=f"D{n}",
            cpf=f"{n + 100000:011d}",
            departamento="SI",
        )

    return _criar


@pytest.fixture
def criar_aluno(criar_usuario):
    def _criar():
        n = next(_seq)
        return Aluno.objects.create(
            usuario=criar_usuario(TipoUsuario.ALUNO),
            matricula=f"A{n}",
            cpf=f"{n + 200000:011d}",
            curso=Curso.objects.first(),  # os 3 cursos vem da migration 0002
        )

    return _criar


@pytest.fixture
def membro_externo(criar_usuario):
    return MembroExterno.objects.create(
        usuario=criar_usuario(TipoUsuario.MEMBRO_EXTERNO), instituicao_origem="UFAM"
    )


@pytest.fixture
def orientador(criar_docente):
    return criar_docente()


@pytest.fixture
def outros_docentes(criar_docente):
    return [criar_docente() for _ in range(4)]


@pytest.fixture
def aluno(criar_aluno):
    return criar_aluno()


@pytest.fixture
def area(db):
    return AreaConhecimento.objects.create(nome="Engenharia de Software")


@pytest.fixture
def dados_tcc(aluno, orientador, area):
    """Um TCC valido. Os testes de erro copiam e trocam um campo."""
    return {
        "titulo": "Sistema de gestao de TCC",
        "area_conhecimento": area,
        "modalidade": "DEFESA_EM_BANCA",
        "autor": aluno,
        "orientador": orientador,
    }


@pytest.fixture
def tcc(dados_tcc, orientador):
    return servico_tcc.cadastrar_tcc(dados=dados_tcc, usuario=orientador.usuario)


@pytest.fixture
def dados_banca(tcc, orientador, outros_docentes):
    """Uma banca valida: orientador + 2 docentes titulares, 1 suplente, daqui a 7 dias."""
    return {
        "tcc": tcc,
        "titulares": [
            orientador.usuario,
            outros_docentes[0].usuario,
            outros_docentes[1].usuario,
        ],
        "suplentes": [outros_docentes[2].usuario],
        "data_hora": timezone.now() + timedelta(days=7),
        "tipo_local": "PRESENCIAL",
        "local": "Sala 10, NUCOMP",
    }


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def api_como(api):
    """APIClient ja logado como o usuario dado (dispensa o login da B5)."""

    def _login(usuario):
        api.force_authenticate(user=usuario)
        return api

    return _login
