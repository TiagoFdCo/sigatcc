"""C9 (3.2): campos e restricoes do DER v2 de 08/11 (D4, D5, D15, D16, D17)."""

import importlib
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import (
    Avaliacao,
    Banca,
    HistoricoStatus,
    ParticipacaoBanca,
    Publicacao,
    ReuniaoAlinhamento,
    SolicitacaoOrientacao,
)
from core.services import tcc as servico_tcc

pytestmark = pytest.mark.django_db

dados_0005 = importlib.import_module("core.migrations.0005_modelo_v2_dados")


def _banca(tcc, **campos):
    dados = {
        "tcc": tcc,
        "data_hora_inicio": timezone.now() + timedelta(days=7),
        "tipo_local": "PRESENCIAL",
        "bloco": "NUCOMP",
        "sala": "10",
    }
    dados.update(campos)
    return Banca.objects.create(**dados)


# ------------------------------------------------------------------ banca
def test_termino_da_defesa_e_inicio_mais_duas_horas(tcc):
    banca = _banca(tcc)
    assert banca.data_hora_fim == banca.data_hora_inicio + timedelta(hours=2)


@pytest.mark.parametrize("campo", ["bloco", "sala"])
def test_banca_presencial_sem_bloco_ou_sala_e_recusada(tcc, campo):
    with pytest.raises(IntegrityError), transaction.atomic():
        _banca(tcc, **{campo: None})


def test_banca_remota_sem_link_e_recusada(tcc):
    with pytest.raises(IntegrityError), transaction.atomic():
        _banca(tcc, tipo_local="REMOTO", bloco=None, sala=None)


def test_banca_remota_so_com_link_e_aceita(tcc):
    banca = _banca(
        tcc,
        tipo_local="REMOTO",
        bloco=None,
        sala=None,
        link_remoto="https://meet.exemplo.com/x",
    )
    assert banca.link_remoto


# -------------------------------------------------------------- avaliacao
def _participacao(tcc, orientador):
    return ParticipacaoBanca.objects.create(
        banca=_banca(tcc), usuario=orientador.usuario, tipo_membro="TITULAR"
    )


@pytest.mark.parametrize("nota", [Decimal("-0.01"), Decimal("10.01")])
def test_nota_fora_de_0_a_10_e_recusada(tcc, orientador, nota):
    participacao = _participacao(tcc, orientador)
    with pytest.raises(IntegrityError), transaction.atomic():
        Avaliacao.objects.create(participacao=participacao, nota=nota, parecer="Ok")


@pytest.mark.parametrize("nota", [Decimal(0), Decimal("7.25"), Decimal(10)])
def test_nota_de_0_a_10_com_parecer_e_aceita(tcc, orientador, nota):
    avaliacao = Avaliacao.objects.create(
        participacao=_participacao(tcc, orientador), nota=nota, parecer="Bom trabalho"
    )
    assert avaliacao.lancada_em is not None


# ------------------------------------------------------------- publicacao
def _publicacao(tcc, **campos):
    dados = {
        "tcc": tcc,
        "periodico": "RBIE",
        "issn_doi": "1414-5685",
        "data_publicacao": timezone.localdate(),
        "comprovante_arquivo_path": None,
        "link_artigo": None,
    }
    dados.update(campos)
    return Publicacao.objects.create(**dados)


def test_publicacao_sem_comprovante_e_sem_link_e_recusada(tcc):
    with pytest.raises(IntegrityError), transaction.atomic():
        _publicacao(tcc)


@pytest.mark.parametrize(
    "campos",
    [
        {"link_artigo": "https://periodico.exemplo.com/artigo"},
        {"comprovante_arquivo_path": "comprovantes/a.pdf"},
    ],
)
def test_publicacao_com_comprovante_ou_link_e_aceita(tcc, campos):
    assert _publicacao(tcc, **campos).pk


# ------------------------------------------------------ historico de status
def test_historico_guarda_quem_mudou_o_status(tcc, orientador):
    servico_tcc.mudar_situacao(
        tcc_id=tcc.pk, status="APRESENTADO", usuario=orientador.usuario
    )
    autores = set(
        HistoricoStatus.objects.filter(tcc=tcc).values_list("alterado_por", flat=True)
    )
    assert autores == {orientador.usuario.pk}


def test_historico_sem_autor_e_recusado(tcc):
    with pytest.raises(IntegrityError), transaction.atomic():
        HistoricoStatus.objects.create(tcc=tcc, status="APRESENTADO")


# ------------------------------------------------ orientacao e reuniao (E3)
def test_solicitacao_sem_mensagem_e_recusa_sem_motivo_sao_aceitas(aluno, orientador):
    solicitacao = SolicitacaoOrientacao.objects.create(
        aluno=aluno, docente=orientador, status="RECUSADA"
    )
    assert solicitacao.mensagem is None
    assert solicitacao.enviada_em is not None
    assert solicitacao.respondida_em is None


def test_reuniao_com_tipo_de_local_fora_da_lista_e_recusada(aluno, orientador):
    solicitacao = SolicitacaoOrientacao.objects.create(
        aluno=aluno, docente=orientador, status="ACEITA"
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        ReuniaoAlinhamento.objects.create(
            solicitacao=solicitacao,
            data_hora=timezone.now() + timedelta(days=1),
            tipo_local="HIBRIDO",
            local="Sala 3",
        )


# ------------------------------------------ migration 0005: local antigo
@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("Sala 10, bloco NUCOMP", ("NUCOMP", "10")),
        ("Bloco B / Sala 204", ("B", "204")),
        ("Sala 10, NUCOMP", ("NUCOMP", "10")),
        ("bloco: C", ("C", "A definir")),
        ("Auditório principal", ("A definir", "Auditório principal")),
        ("", ("A definir", "A definir")),
    ],
)
def test_dividir_local_antigo_em_bloco_e_sala(texto, esperado):
    assert dados_0005.dividir_local(texto) == esperado
