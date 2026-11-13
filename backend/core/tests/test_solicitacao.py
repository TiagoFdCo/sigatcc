"""C3a (7.2): solicitacao e aceite de orientacao (RBN46, RBN47, RD20; PF41 a PF43, PF63).

Criterio de aceite do pacote: so aluno sem TCC ativo solicita; resposta unica;
apos o aceite, o TCC pode ser cadastrado com esse orientador.
"""

import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import Docente, LogAuditoria, SolicitacaoOrientacao, Usuario
from core.services import solicitacao as servico

pytestmark = pytest.mark.django_db

URL = "/api/solicitacoes-orientacao/"


@pytest.fixture
def aluno_livre(criar_aluno):
    """Aluno sem TCC: pode solicitar orientacao."""
    return criar_aluno()


def _enviar(aluno, docente, mensagem=None):
    return servico.enviar_solicitacao(
        aluno=aluno, docente=docente, mensagem=mensagem, usuario=aluno.usuario
    )


def _logs(solicitacao):
    return LogAuditoria.objects.filter(
        entidade="SOLICITACAO_ORIENTACAO", registro_id=solicitacao.pk
    )


# ------------------------------------------------------------- envio (PF41)
def test_aluno_sem_tcc_envia_solicitacao(aluno_livre, orientador):
    s = _enviar(aluno_livre, orientador, "  Tenho interesse em IoT  ")
    assert s.status == "PENDENTE"
    assert s.mensagem == "Tenho interesse em IoT"
    assert s.enviada_em is not None and s.respondida_em is None
    assert _logs(s).filter(campo="status", valor_novo="PENDENTE").count() == 1


def test_mensagem_e_opcional(aluno_livre, orientador):
    assert _enviar(aluno_livre, orientador, "   ").mensagem is None


def test_aluno_com_tcc_ativo_nao_solicita(tcc, criar_docente):
    with pytest.raises(ValidationError, match="TCC ativo"):
        _enviar(tcc.autor, criar_docente())


def test_docente_que_nao_aceita_orientacoes_nao_recebe(aluno_livre, orientador):
    Docente.objects.filter(pk=orientador.pk).update(aceita_orientacoes=False)
    orientador = Docente.objects.select_related("usuario").get(pk=orientador.pk)
    with pytest.raises(ValidationError, match="não está aceitando"):
        _enviar(aluno_livre, orientador)


def test_docente_inativo_nao_recebe(aluno_livre, orientador):
    Usuario.objects.filter(pk=orientador.pk).update(ativo=False)
    orientador = Docente.objects.select_related("usuario").get(pk=orientador.pk)
    with pytest.raises(ValidationError, match="não está aceitando"):
        _enviar(aluno_livre, orientador)


def test_segunda_pendente_para_o_mesmo_docente_e_recusada(aluno_livre, orientador):
    _enviar(aluno_livre, orientador)
    with pytest.raises(ValidationError, match="pendente"):
        _enviar(aluno_livre, orientador)


def test_pode_solicitar_a_docentes_diferentes(aluno_livre, orientador, criar_docente):
    _enviar(aluno_livre, orientador)
    assert _enviar(aluno_livre, criar_docente()).status == "PENDENTE"


def test_com_orientacao_aceita_nao_solicita_de_novo(
    aluno_livre, orientador, criar_docente
):
    s = _enviar(aluno_livre, orientador)
    servico.responder_solicitacao(
        solicitacao_id=s.pk, status="ACEITA", usuario=orientador.usuario
    )
    with pytest.raises(ValidationError, match="orientação aceita"):
        _enviar(aluno_livre, criar_docente())


# --------------------------------------------------------- resposta (PF42)
def test_docente_aceita_uma_unica_vez(aluno_livre, orientador):
    s = _enviar(aluno_livre, orientador)
    s = servico.responder_solicitacao(
        solicitacao_id=s.pk, status="ACEITA", usuario=orientador.usuario
    )
    assert s.status == "ACEITA" and s.respondida_em is not None
    assert _logs(s).filter(valor_anterior="PENDENTE", valor_novo="ACEITA").exists()
    with pytest.raises(ValidationError, match="já foi respondida"):
        servico.responder_solicitacao(
            solicitacao_id=s.pk, status="RECUSADA", usuario=orientador.usuario
        )


@pytest.mark.parametrize("motivo, esperado", [(None, None), (" Sem vaga ", "Sem vaga")])
def test_recusa_com_ou_sem_motivo(aluno_livre, orientador, motivo, esperado):
    s = _enviar(aluno_livre, orientador)
    s = servico.responder_solicitacao(
        solicitacao_id=s.pk,
        status="RECUSADA",
        motivo_recusa=motivo,
        usuario=orientador.usuario,
    )
    assert (s.status, s.motivo_recusa) == ("RECUSADA", esperado)


def test_aceite_descarta_motivo(aluno_livre, orientador):
    s = _enviar(aluno_livre, orientador)
    s = servico.responder_solicitacao(
        solicitacao_id=s.pk,
        status="ACEITA",
        motivo_recusa="não se aplica",
        usuario=orientador.usuario,
    )
    assert s.motivo_recusa is None


def test_outro_docente_nao_responde(aluno_livre, orientador, criar_docente):
    s = _enviar(aluno_livre, orientador)
    with pytest.raises(PermissionDenied):
        servico.responder_solicitacao(
            solicitacao_id=s.pk, status="ACEITA", usuario=criar_docente().usuario
        )


def test_resposta_invalida_e_recusada(aluno_livre, orientador):
    s = _enviar(aluno_livre, orientador)
    with pytest.raises(ValidationError, match="ACEITA ou RECUSADA"):
        servico.responder_solicitacao(
            solicitacao_id=s.pk, status="PENDENTE", usuario=orientador.usuario
        )


# ------------------------------------------------------------------- API
def test_api_aluno_envia_e_ve_so_as_suas(
    api_como, aluno_livre, orientador, criar_aluno
):
    outro = criar_aluno()
    _enviar(outro, orientador)
    cliente = api_como(aluno_livre.usuario)
    resp = cliente.post(URL, {"docente": str(orientador.pk)}, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["docente_nome"] == orientador.usuario.nome_completo
    lista = cliente.get(URL)
    assert [s["id"] for s in lista.data] == [resp.data["id"]]


def test_api_docente_nao_envia(api_como, orientador, criar_docente):
    resp = api_como(orientador.usuario).post(
        URL, {"docente": str(criar_docente().pk)}, format="json"
    )
    assert resp.status_code == 403


def test_api_docente_ve_as_recebidas_e_responde(
    api_como, aluno_livre, orientador, criar_docente
):
    minha = _enviar(aluno_livre, orientador)
    _enviar(aluno_livre, criar_docente())
    cliente = api_como(orientador.usuario)
    assert [s["id"] for s in cliente.get(URL).data] == [str(minha.pk)]
    resp = cliente.post(
        f"{URL}{minha.pk}/responder/", {"status": "ACEITA"}, format="json"
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["status"] == "ACEITA"


def test_api_outro_docente_nao_responde(
    api_como, aluno_livre, orientador, criar_docente
):
    s = _enviar(aluno_livre, orientador)
    resp = api_como(criar_docente().usuario).post(
        f"{URL}{s.pk}/responder/", {"status": "ACEITA"}, format="json"
    )
    assert resp.status_code == 403
    s.refresh_from_db()
    assert s.status == "PENDENTE"


def test_api_aluno_com_tcc_recebe_400_no_campo(api_como, tcc, criar_docente):
    resp = api_como(tcc.autor.usuario).post(
        URL, {"docente": str(criar_docente().pk)}, format="json"
    )
    assert resp.status_code == 400
    assert "aluno" in resp.data


def test_api_professor_tcc_ve_todas(api_como, professor_tcc, aluno_livre, orientador):
    _enviar(aluno_livre, orientador)
    assert len(api_como(professor_tcc.usuario).get(URL).data) == 1


def test_api_filtro_por_status(api_como, aluno_livre, orientador, criar_docente):
    s = _enviar(aluno_livre, orientador)
    _enviar(aluno_livre, criar_docente())
    servico.responder_solicitacao(
        solicitacao_id=s.pk, status="RECUSADA", usuario=orientador.usuario
    )
    resp = api_como(aluno_livre.usuario).get(URL, {"status": "PENDENTE"})
    assert len(resp.data) == 1


def test_api_sem_login_devolve_401(api, orientador):
    assert api.get(URL).status_code == 401


# ------------------------------------------------- busca de orientador (PF63)
def test_busca_de_orientador_mostra_carga_e_areas(
    api_como, aluno_livre, orientador, tcc, area
):
    orientador.areas_interesse.add(area)
    resp = api_como(aluno_livre.usuario).get("/api/orientadores/")
    assert resp.status_code == 200
    item = next(d for d in resp.data if d["id"] == str(orientador.pk))
    assert item["qtd_orientacoes"] == 1
    assert item["areas_interesse"] == [{"id": str(area.pk), "nome": area.nome}]
    assert "cpf" not in item and "matricula_institucional" not in item


def test_busca_de_orientador_filtra_por_area_e_nome(
    api_como, aluno_livre, orientador, criar_docente, area
):
    orientador.areas_interesse.add(area)
    criar_docente()
    cliente = api_como(aluno_livre.usuario)
    por_area = cliente.get("/api/orientadores/", {"area": str(area.pk)}).data
    assert [d["id"] for d in por_area] == [str(orientador.pk)]
    nome = orientador.usuario.nome_completo.split()[0]
    por_nome = cliente.get("/api/orientadores/", {"busca": nome}).data
    assert str(orientador.pk) in [d["id"] for d in por_nome]
    assert cliente.get("/api/orientadores/", {"area": "x"}).data == []


def test_busca_de_orientador_esconde_docente_inativo(api_como, aluno_livre, orientador):
    Usuario.objects.filter(pk=orientador.pk).update(ativo=False)
    resp = api_como(aluno_livre.usuario).get("/api/orientadores/")
    assert str(orientador.pk) not in [d["id"] for d in resp.data]


def test_solicitacao_guarda_quem_procurou_quem(aluno_livre, orientador):
    s = _enviar(aluno_livre, orientador)
    assert SolicitacaoOrientacao.objects.get(pk=s.pk).docente == orientador
