"""Testes do que a interface de TCC (B9b) usa da API: nomes, filtros e historico."""

import pytest

from core.models import TCC, Curso
from core.services import tcc as servico_tcc

pytestmark = pytest.mark.django_db

URL = "/api/tccs/"


@pytest.fixture
def dois_tccs(tcc, criar_aluno, criar_docente, area, orientador):
    """O TCC da fixture e mais um, por publicacao, de outro aluno e orientador."""
    outro_orientador = criar_docente()
    outro_orientador.usuario.nome_completo = "Teodoro Brandão"
    outro_orientador.usuario.save()
    outro = servico_tcc.cadastrar_tcc(
        dados={
            "titulo": "Jogos no ensino de lógica",
            "area_conhecimento": area,
            "modalidade": "PUBLICACAO_APROVADA",
            "autor": criar_aluno(),
            "orientador": outro_orientador,
        },
        usuario=orientador.usuario,
    )
    return tcc, outro


def test_listagem_traz_nomes_para_a_tela(api_como, orientador, tcc):
    resp = api_como(orientador.usuario).get(URL)
    item = resp.data[0]
    assert item["autor_nome"] == tcc.autor.usuario.nome_completo
    assert item["orientador_nome"] == orientador.usuario.nome_completo
    assert item["coorientador_nome"] is None
    assert item["curso_nome"] == tcc.curso.nome
    assert item["area_nome"] == tcc.area_conhecimento.nome


@pytest.mark.parametrize(
    "params, esperado",
    [
        ({"busca": "lógica"}, "Jogos no ensino de lógica"),
        ({"busca": "teodoro"}, "Jogos no ensino de lógica"),
        ({"modalidade": "DEFESA_EM_BANCA"}, "Sistema de gestao de TCC"),
        (
            {"status": "EM_DESENVOLVIMENTO", "modalidade": "PUBLICACAO_APROVADA"},
            "Jogos no ensino de lógica",
        ),
    ],
)
def test_filtros_da_listagem(api_como, orientador, dois_tccs, params, esperado):
    resp = api_como(orientador.usuario).get(URL, params)
    assert [t["titulo"] for t in resp.data] == [esperado]


def test_filtro_por_curso_e_id_invalido(api_como, orientador, dois_tccs):
    cliente = api_como(orientador.usuario)
    curso = dois_tccs[0].curso
    outro_curso = Curso.objects.exclude(pk=curso.pk).first()

    assert len(cliente.get(URL, {"curso": str(curso.pk)}).data) == 2
    assert cliente.get(URL, {"curso": str(outro_curso.pk)}).data == []
    resp = cliente.get(URL, {"curso": "nao-e-uuid"})
    assert resp.status_code == 200
    assert resp.data == []


def test_filtro_ativo(api_como, orientador, dois_tccs):
    TCC.objects.filter(pk=dois_tccs[1].pk).update(ativo=False, motivo_inativacao="Erro")
    resp = api_como(orientador.usuario).get(URL, {"ativo": "true"})
    assert [t["id"] for t in resp.data] == [str(dois_tccs[0].pk)]


def test_detalhe_traz_historico(api_como, orientador, tcc):
    servico_tcc.mudar_situacao(
        tcc_id=tcc.pk, status="APRESENTADO", usuario=orientador.usuario
    )
    resp = api_como(orientador.usuario).get(f"{URL}{tcc.pk}/")
    assert resp.status_code == 200
    assert [h["status"] for h in resp.data["historico"]] == [
        "APRESENTADO",
        "EM_DESENVOLVIMENTO",
    ]


def test_mudar_situacao_responde_com_historico(api_como, orientador, tcc):
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc.pk}/situacao/", {"status": "APRESENTADO"}, format="json"
    )
    assert resp.status_code == 200
    assert len(resp.data["historico"]) == 2
