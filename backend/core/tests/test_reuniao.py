"""C3b (7.3): reuniao de alinhamento (RBN48, RD21; PF44 e PF45).

Criterio de aceite do pacote: so apos o aceite; conflito de agenda e alertado.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import LogAuditoria, ReuniaoAlinhamento
from core.services import banca as servico_banca
from core.services import reuniao as servico
from core.services import solicitacao as servico_solicitacao

pytestmark = pytest.mark.django_db

URL = "/api/solicitacoes-orientacao/"


def _amanha(horas=10):
    base = timezone.localtime() + timedelta(days=1)
    return base.replace(hour=horas, minute=0, second=0, microsecond=0)


def _solicitar(aluno, docente):
    return servico_solicitacao.enviar_solicitacao(
        aluno=aluno, docente=docente, usuario=aluno.usuario
    )


def _aceitar(solicitacao):
    return servico_solicitacao.responder_solicitacao(
        solicitacao_id=solicitacao.pk,
        status="ACEITA",
        usuario=solicitacao.docente.usuario,
    )


@pytest.fixture
def aceita(criar_aluno, orientador):
    return _aceitar(_solicitar(criar_aluno(), orientador))


def _agendar(solicitacao, usuario, **campos):
    dados = {
        "data_hora": _amanha(),
        "tipo_local": "PRESENCIAL",
        "local": "Sala 3, NUCOMP",
    }
    dados.update(campos)
    return servico.agendar_reuniao(
        solicitacao_id=solicitacao.pk, usuario=usuario, **dados
    )


# ---------------------------------------------------------------- servico
def test_docente_agenda_depois_do_aceite(aceita, orientador):
    reuniao, criada, alertas = _agendar(aceita, orientador.usuario)
    assert criada and alertas == []
    assert reuniao.local == "Sala 3, NUCOMP"
    assert LogAuditoria.objects.filter(
        entidade="REUNIAO_ALINHAMENTO", registro_id=reuniao.pk
    ).exists()


def test_aluno_tambem_agenda(aceita):
    _, criada, _ = _agendar(aceita, aceita.aluno.usuario)
    assert criada


def test_agendar_de_novo_remarca_a_mesma_reuniao(aceita, orientador):
    primeira, _, _ = _agendar(aceita, orientador.usuario)
    segunda, criada, _ = _agendar(
        aceita,
        orientador.usuario,
        data_hora=_amanha(15),
        tipo_local="REMOTO",
        local="https://meet.exemplo.com/x",
    )
    assert not criada and segunda.pk == primeira.pk
    assert ReuniaoAlinhamento.objects.count() == 1
    campos = set(
        LogAuditoria.objects.filter(registro_id=primeira.pk).values_list(
            "campo", flat=True
        )
    )
    assert {"data_hora", "tipo_local", "local"} <= campos


@pytest.mark.parametrize("status", ["PENDENTE", "RECUSADA"])
def test_so_depois_do_aceite(criar_aluno, orientador, status):
    s = _solicitar(criar_aluno(), orientador)
    if status == "RECUSADA":
        servico_solicitacao.responder_solicitacao(
            solicitacao_id=s.pk, status="RECUSADA", usuario=orientador.usuario
        )
    with pytest.raises(ValidationError, match="depois do aceite"):
        _agendar(s, orientador.usuario)


def test_quem_nao_participa_nao_agenda(aceita, criar_docente):
    with pytest.raises(PermissionDenied):
        _agendar(aceita, criar_docente().usuario)


def test_data_passada_e_recusada(aceita, orientador):
    with pytest.raises(ValidationError, match="futura"):
        _agendar(aceita, orientador.usuario, data_hora=timezone.now())


@pytest.mark.parametrize(
    "tipo, local, erro",
    [("PRESENCIAL", "  ", "Informe o local"), ("REMOTO", "Sala 3", "link válido")],
)
def test_local_invalido_e_recusado(aceita, orientador, tipo, local, erro):
    with pytest.raises(ValidationError, match=erro):
        _agendar(aceita, orientador.usuario, tipo_local=tipo, local=local)


def test_conflito_com_outra_reuniao_do_docente_e_alertado(
    aceita, orientador, criar_aluno
):
    _agendar(aceita, orientador.usuario)
    outra = _aceitar(_solicitar(criar_aluno(), orientador))
    reuniao, _, alertas = _agendar(
        outra, orientador.usuario, data_hora=_amanha() + timedelta(minutes=30)
    )
    assert reuniao.pk  # alerta, mas grava
    assert any("O docente já tem reunião" in a for a in alertas)


def test_reunioes_encostadas_nao_conflitam(aceita, orientador, criar_aluno):
    _agendar(aceita, orientador.usuario)
    outra = _aceitar(_solicitar(criar_aluno(), orientador))
    _, _, alertas = _agendar(
        outra, orientador.usuario, data_hora=_amanha() + timedelta(hours=1)
    )
    assert alertas == []


def test_conflito_com_banca_do_docente_e_alertado(
    aceita, orientador, tcc, outros_docentes
):
    servico_banca.cadastrar_banca(
        tcc=tcc,
        titulares=[
            orientador.usuario,
            outros_docentes[0].usuario,
            outros_docentes[1].usuario,
        ],
        data_hora_inicio=_amanha(9),
        tipo_local="PRESENCIAL",
        bloco="NUCOMP",
        sala="10",
        usuario=orientador.usuario,
    )
    _, _, alertas = _agendar(aceita, orientador.usuario, data_hora=_amanha(10))
    assert any("banca" in a for a in alertas)


# ------------------------------------------------------------------- API
def test_api_agendar_devolve_201_e_depois_200(api_como, aceita, orientador):
    cliente = api_como(orientador.usuario)
    corpo = {
        "data_hora": _amanha().isoformat(),
        "tipo_local": "PRESENCIAL",
        "local": "Sala 3",
    }
    resp = cliente.post(f"{URL}{aceita.pk}/reuniao/", corpo, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["alertas"] == []
    resp = cliente.post(f"{URL}{aceita.pk}/reuniao/", corpo, format="json")
    assert resp.status_code == 200
    detalhe = cliente.get(f"{URL}{aceita.pk}/").data
    assert detalhe["reuniao"]["local"] == "Sala 3"


def test_api_reunioes_de_cada_um(api_como, aceita, orientador, criar_docente):
    _agendar(aceita, orientador.usuario)
    assert len(api_como(aceita.aluno.usuario).get("/api/reunioes/").data) == 1
    assert len(api_como(orientador.usuario).get("/api/reunioes/").data) == 1
    assert api_como(criar_docente().usuario).get("/api/reunioes/").data == []


def test_api_reunioes_futuras(api_como, aceita, orientador):
    reuniao, _, _ = _agendar(aceita, orientador.usuario)
    ReuniaoAlinhamento.objects.filter(pk=reuniao.pk).update(
        data_hora=timezone.now() - timedelta(days=1)
    )
    cliente = api_como(orientador.usuario)
    assert len(cliente.get("/api/reunioes/").data) == 1
    assert cliente.get("/api/reunioes/", {"futuras": "true"}).data == []
