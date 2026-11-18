"""Testes da C2a: o aluno ve so o proprio TCC (aceite do item 4.2 da EAP)."""

import pytest

from core.models import Visibilidade
from core.services import tcc as servico_tcc

pytestmark = pytest.mark.django_db

URL = "/api/tccs/"


@pytest.fixture
def tcc_de_outro(criar_aluno, orientador, area):
    """Um TCC restrito de outra pessoa, que o aluno nao pode abrir."""
    outro = criar_aluno()
    return servico_tcc.cadastrar_tcc(
        dados={
            "titulo": "Segredo industrial de outro aluno",
            "area_conhecimento": area,
            "modalidade": "DEFESA_EM_BANCA",
            "autor": outro,
            "orientador": orientador,
            "visibilidade": Visibilidade.RESTRITO,
        },
        usuario=orientador.usuario,
    )


def _ids(resposta):
    return {t["id"] for t in resposta.data}


# ================================================================== TCCs
def test_aluno_lista_so_o_proprio_tcc(api_como, aluno, tcc, tcc_de_outro):
    resp = api_como(aluno.usuario).get(URL)

    assert resp.status_code == 200
    assert _ids(resp) == {str(tcc.pk)}


def test_aluno_abre_o_proprio_tcc(api_como, aluno, tcc):
    resp = api_como(aluno.usuario).get(f"{URL}{tcc.pk}/")
    assert resp.status_code == 200
    assert resp.data["titulo"] == tcc.titulo


def test_aluno_nao_abre_o_tcc_de_outra_pessoa(api_como, aluno, tcc, tcc_de_outro):
    resp = api_como(aluno.usuario).get(f"{URL}{tcc_de_outro.pk}/")
    assert resp.status_code == 403  # escopo do C17: recusa e registra, nao 404


def test_busca_do_aluno_nao_vaza_tcc_de_outro(api_como, aluno, tcc, tcc_de_outro):
    resp = api_como(aluno.usuario).get(URL, {"busca": "Segredo industrial"})
    assert resp.status_code == 200
    assert _ids(resp) == set()


def test_aluno_sem_tcc_ve_lista_vazia(api_como, criar_aluno, tcc_de_outro):
    resp = api_como(criar_aluno().usuario).get(URL)
    assert resp.status_code == 200
    assert _ids(resp) == set()


def test_docente_e_secretaria_continuam_vendo_todos(
    api_como, orientador, criar_usuario, tcc, tcc_de_outro
):
    esperado = {str(tcc.pk), str(tcc_de_outro.pk)}
    for quem in (orientador.usuario, criar_usuario("SECRETARIA")):
        assert _ids(api_como(quem).get(URL)) == esperado


def test_aluno_nao_escreve_em_tcc(api_como, aluno, tcc):
    cliente = api_como(aluno.usuario)
    assert (
        cliente.patch(f"{URL}{tcc.pk}/", {"titulo": "X"}, format="json").status_code
        == 403
    )
    assert cliente.post(URL, {}, format="json").status_code == 403
    assert (
        cliente.post(
            f"{URL}{tcc.pk}/situacao/", {"status": "NAO_APRESENTADO"}, format="json"
        ).status_code
        == 403
    )


# ======================================================== bancas e docentes
def test_aluno_nao_acessa_docentes(api_como, aluno, tcc):
    """O aluno busca orientador por /api/orientadores/ (C3a), sem CPF nem matricula."""
    assert api_como(aluno.usuario).get("/api/docentes/").status_code == 403


def test_aluno_ve_so_bancas_do_proprio_tcc(api_como, criar_aluno, tcc):
    """Bancas seguem o escopo do C17; quem nao tem TCC recebe lista vazia."""
    resp = api_como(criar_aluno().usuario).get("/api/bancas/")
    assert resp.status_code == 200
    assert list(resp.data) == []


def test_docente_e_secretaria_continuam_acessando_bancas_e_docentes(
    api_como, orientador, criar_usuario
):
    for quem in (orientador.usuario, criar_usuario("SECRETARIA")):
        cliente = api_como(quem)
        for rota in ("/api/bancas/", "/api/docentes/"):
            assert cliente.get(rota).status_code == 200, (quem.tipo_usuario, rota)


def test_areas_continuam_abertas_ao_aluno(api_como, aluno, area):
    """O 'Meu perfil' precisa listar as areas para o aluno escolher as de interesse."""
    resp = api_como(aluno.usuario).get("/api/areas/")
    assert resp.status_code == 200
    assert area.nome in {a["nome"] for a in resp.data}
