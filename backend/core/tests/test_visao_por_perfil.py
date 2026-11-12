"""C17 (4.7): visao por perfil, Orientador x Professor de TCC (RBN56, RD29, RNF03).

Criterio de aceite do pacote: o Orientador nao abre nem edita TCC de outro
orientador (acesso negado e registrado); teste na matriz perfil x acao.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from core.models import TCC, Banca, LogAuditoria
from core.services import banca as servico_banca
from core.services import tcc as servico_tcc

pytestmark = pytest.mark.django_db

URL = "/api/tccs/"


@pytest.fixture
def outro_orientador(criar_docente):
    return criar_docente()


@pytest.fixture
def tcc_alheio(criar_aluno, outro_orientador, area):
    """TCC orientado por outro docente (fora do escopo do `orientador`)."""
    return servico_tcc.cadastrar_tcc(
        dados={
            "titulo": "TCC de outro orientador",
            "area_conhecimento": area,
            "modalidade": "DEFESA_EM_BANCA",
            "autor": criar_aluno(),
            "orientador": outro_orientador,
        },
        usuario=outro_orientador.usuario,
    )


def _ids(resp):
    assert resp.status_code == 200, resp.data
    return {t["id"] for t in resp.data}


def _negacoes(tcc):
    return LogAuditoria.objects.filter(
        entidade="TCC", registro_id=tcc.pk, campo="acesso_negado"
    )


# ------------------------------------------------------------- listagem
def test_orientador_lista_so_os_tccs_que_orienta(api_como, orientador, tcc, tcc_alheio):
    assert _ids(api_como(orientador.usuario).get(URL)) == {str(tcc.pk)}


def test_coorientador_tambem_ve_o_tcc(api_como, criar_docente, tcc):
    co = criar_docente()
    TCC.objects.filter(pk=tcc.pk).update(coorientador=co)
    assert _ids(api_como(co.usuario).get(URL)) == {str(tcc.pk)}


@pytest.mark.parametrize("perfil", ["professor_tcc", "ADMINISTRADOR", "SECRETARIA"])
def test_perfis_que_veem_todos(
    api_como, criar_usuario, professor_tcc, tcc, tcc_alheio, perfil
):
    usuario = (
        professor_tcc.usuario if perfil == "professor_tcc" else criar_usuario(perfil)
    )
    assert _ids(api_como(usuario).get(URL)) == {str(tcc.pk), str(tcc_alheio.pk)}


def test_secretaria_ve_tcc_restrito(api_como, criar_usuario, tcc):
    """RBN55: a visao por perfil nao esconde da Secretaria o TCC restrito."""
    assert tcc.visibilidade == "RESTRITO"
    resp = api_como(criar_usuario("SECRETARIA")).get(f"{URL}{tcc.pk}/")
    assert resp.status_code == 200
    assert resp.data["pode_editar"] is False


def test_aluno_ve_so_o_proprio_tcc(api_como, tcc, tcc_alheio):
    cliente = api_como(tcc.autor.usuario)
    assert _ids(cliente.get(URL)) == {str(tcc.pk)}
    assert cliente.get(f"{URL}{tcc.pk}/").status_code == 200
    assert cliente.get(f"{URL}{tcc_alheio.pk}/").status_code == 403


def test_membro_externo_nao_lista_tccs(api_como, membro_externo, tcc):
    assert _ids(api_como(membro_externo.usuario).get(URL)) == set()


# ------------------------------------------------- detalhe fora do escopo
def test_orientador_nao_abre_tcc_alheio_e_a_tentativa_fica_registrada(
    api_como, orientador, tcc_alheio
):
    resp = api_como(orientador.usuario).get(f"{URL}{tcc_alheio.pk}/")
    assert resp.status_code == 403
    log = _negacoes(tcc_alheio).get()
    assert log.responsavel == orientador.usuario
    assert log.valor_novo == "GET retrieve"


def test_tcc_inexistente_continua_404(api_como, orientador):
    resp = api_como(orientador.usuario).get(
        f"{URL}00000000-0000-0000-0000-000000000000/"
    )
    assert resp.status_code == 404


# ------------------------------------------------- escrita fora do escopo
def test_orientador_nao_edita_tcc_alheio(api_como, orientador, tcc_alheio):
    resp = api_como(orientador.usuario).patch(
        f"{URL}{tcc_alheio.pk}/", {"titulo": "Invadido"}, format="json"
    )
    assert resp.status_code == 403
    tcc_alheio.refresh_from_db()
    assert tcc_alheio.titulo == "TCC de outro orientador"
    assert _negacoes(tcc_alheio).filter(valor_novo="PATCH partial_update").exists()


def test_orientador_nao_muda_situacao_de_tcc_alheio(api_como, orientador, tcc_alheio):
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc_alheio.pk}/situacao/", {"status": "APRESENTADO"}, format="json"
    )
    assert resp.status_code == 403
    tcc_alheio.refresh_from_db()
    assert tcc_alheio.status == "EM_DESENVOLVIMENTO"
    assert _negacoes(tcc_alheio).filter(valor_novo="POST situacao").exists()


def test_orientador_nao_registra_publicacao_de_tcc_alheio(
    api_como, orientador, tcc_alheio
):
    TCC.objects.filter(pk=tcc_alheio.pk).update(modalidade="PUBLICACAO_APROVADA")
    resp = api_como(orientador.usuario).post(
        f"{URL}{tcc_alheio.pk}/publicacao/", {}, format="json"
    )
    assert resp.status_code == 403
    assert _negacoes(tcc_alheio).filter(valor_novo="POST publicacao").exists()


def test_professor_tcc_edita_qualquer_tcc(api_como, professor_tcc, tcc_alheio):
    resp = api_como(professor_tcc.usuario).patch(
        f"{URL}{tcc_alheio.pk}/", {"titulo": "Título revisado"}, format="json"
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["pode_editar"] is True


def test_coorientador_edita_o_tcc(api_como, criar_docente, tcc):
    co = criar_docente()
    TCC.objects.filter(pk=tcc.pk).update(coorientador=co)
    resp = api_como(co.usuario).patch(
        f"{URL}{tcc.pk}/", {"titulo": "Novo título"}, format="json"
    )
    assert resp.status_code == 200, resp.data


def test_detalhe_informa_se_o_usuario_pode_editar(
    api_como, orientador, professor_tcc, tcc
):
    assert api_como(orientador.usuario).get(f"{URL}{tcc.pk}/").data["pode_editar"]
    assert api_como(professor_tcc.usuario).get(URL).data[0]["pode_editar"] is True


# ------------------------------------------------------------- cadastro
def _corpo_tcc(aluno, orientador, area):
    return {
        "titulo": "Novo TCC",
        "area_conhecimento": str(area.pk),
        "modalidade": "DEFESA_EM_BANCA",
        "autor": str(aluno.pk),
        "orientador": str(orientador.pk),
    }


def test_orientador_nao_cadastra_tcc_para_outro_docente(
    api_como, orientador, outro_orientador, criar_aluno, area
):
    corpo = _corpo_tcc(criar_aluno(), outro_orientador, area)
    resp = api_como(orientador.usuario).post(URL, corpo, format="json")
    assert resp.status_code == 403
    assert TCC.objects.count() == 0


def test_orientador_cadastra_tcc_que_orienta(api_como, orientador, criar_aluno, area):
    corpo = _corpo_tcc(criar_aluno(), orientador, area)
    assert (
        api_como(orientador.usuario).post(URL, corpo, format="json").status_code == 201
    )


def test_professor_tcc_cadastra_para_qualquer_docente(
    api_como, professor_tcc, outro_orientador, criar_aluno, area
):
    corpo = _corpo_tcc(criar_aluno(), outro_orientador, area)
    resp = api_como(professor_tcc.usuario).post(URL, corpo, format="json")
    assert resp.status_code == 201, resp.data


# ---------------------------------------------------------------- bancas
def _banca_de(tcc, membros):
    return servico_banca.cadastrar_banca(
        tcc=tcc,
        titulares=[tcc.orientador.usuario, *membros],
        data_hora_inicio=timezone.now() + timedelta(days=7),
        tipo_local="PRESENCIAL",
        bloco="NUCOMP",
        sala="10",
        usuario=tcc.orientador.usuario,
    )


def test_orientador_nao_cadastra_banca_de_tcc_alheio(
    api_como, orientador, tcc_alheio, outros_docentes
):
    corpo = {
        "tcc": str(tcc_alheio.pk),
        "titulares": [
            str(tcc_alheio.orientador.pk),
            str(outros_docentes[0].pk),
            str(outros_docentes[1].pk),
        ],
        "data_hora_inicio": (timezone.now() + timedelta(days=7)).isoformat(),
        "tipo_local": "PRESENCIAL",
        "bloco": "NUCOMP",
        "sala": "10",
    }
    resp = api_como(orientador.usuario).post("/api/bancas/", corpo, format="json")
    assert resp.status_code == 403
    assert Banca.objects.count() == 0
    assert _negacoes(tcc_alheio).filter(valor_novo="POST cadastrar banca").exists()


def test_bancas_visiveis_sao_as_do_escopo_e_as_de_que_participa(
    api_como, orientador, tcc, tcc_alheio, outros_docentes, criar_aluno, area
):
    minha = _banca_de(tcc, [outros_docentes[0].usuario, outros_docentes[1].usuario])
    # o orientador e titular na banca de um TCC que nao orienta
    da_qual_participa = _banca_de(
        tcc_alheio, [orientador.usuario, outros_docentes[2].usuario]
    )
    terceiro = servico_tcc.cadastrar_tcc(
        dados={
            "titulo": "Terceiro TCC",
            "area_conhecimento": area,
            "modalidade": "DEFESA_EM_BANCA",
            "autor": criar_aluno(),
            "orientador": tcc_alheio.orientador,
        },
        usuario=tcc_alheio.orientador.usuario,
    )
    _banca_de(terceiro, [outros_docentes[2].usuario, outros_docentes[3].usuario])

    resp = api_como(orientador.usuario).get("/api/bancas/")
    assert resp.status_code == 200
    assert {b["id"] for b in resp.data} == {str(minha.pk), str(da_qual_participa.pk)}
