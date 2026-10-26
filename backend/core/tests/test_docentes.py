"""Testes do B6 (cadastro de docentes pelo administrador)."""

import pytest

from core.models import Docente, LogAuditoria, Usuario
from core.services import banca as servico_banca

pytestmark = pytest.mark.django_db

URL = "/api/docentes/"
CPF_VALIDO = "529.982.247-25"
SENHA = "Inicial#2026"


@pytest.fixture
def admin(criar_usuario):
    return criar_usuario("ADMINISTRADOR")


@pytest.fixture
def corpo(area):
    return {
        "nome_completo": "Marina Lopes",
        "email": "marina.lopes@uea.edu.br",
        "matricula_institucional": "INST-0099",
        "cpf": CPF_VALIDO,
        "departamento": "ECP",
        "areas_interesse": [str(area.pk)],
        "senha_inicial": SENHA,
    }


def _criar(api_como, admin, corpo):
    return api_como(admin).post(URL, corpo, format="json")


# ============================================================= cadastro
def test_admin_cadastra_docente(api_como, admin, corpo, area):
    resp = _criar(api_como, admin, corpo)

    assert resp.status_code == 201, resp.data
    assert resp.data["cpf"] == "***.982.247-**"
    docente = Docente.objects.get(matricula_institucional="INST-0099")
    assert docente.cpf == "52998224725"
    assert docente.usuario.tipo_usuario == "DOCENTE"
    assert docente.usuario.check_password(SENHA)
    assert list(docente.areas_interesse.all()) == [area]
    assert LogAuditoria.objects.filter(entidade="DOCENTE", campo="cadastro").exists()


def test_docente_cadastrado_consegue_entrar(api_como, api, admin, corpo):
    _criar(api_como, admin, corpo)
    api.force_authenticate(user=None)
    resp = api.post(
        "/api/auth/login/", {"login": "INST-0099", "senha": SENHA}, format="json"
    )
    assert resp.status_code == 200


@pytest.mark.parametrize("tipo", ["DOCENTE", "SECRETARIA"])
def test_so_administrador_cadastra(api_como, criar_usuario, corpo, tipo):
    resp = api_como(criar_usuario(tipo)).post(URL, corpo, format="json")
    assert resp.status_code == 403
    assert not Docente.objects.filter(matricula_institucional="INST-0099").exists()


def test_cpf_invalido_e_recusado(api_como, admin, corpo):
    resp = _criar(api_como, admin, {**corpo, "cpf": "529.982.247-24"})
    assert resp.status_code == 400
    assert "cpf" in resp.data


@pytest.mark.parametrize(
    "campo, valor",
    [("email", "MARINA.LOPES@uea.edu.br"), ("matricula_institucional", "INST-0099")],
)
def test_email_e_matricula_repetidos_sao_recusados(
    api_como, admin, corpo, campo, valor
):
    _criar(api_como, admin, corpo)
    outro = {**corpo, "email": "outra@uea.edu.br", "matricula_institucional": "X1"}
    outro["cpf"] = "111.444.777-35"
    outro[campo] = valor
    resp = _criar(api_como, admin, outro)
    assert resp.status_code == 400
    assert campo in resp.data


def test_cpf_repetido_e_recusado(api_como, admin, corpo):
    _criar(api_como, admin, corpo)
    outro = {**corpo, "email": "outra@uea.edu.br", "matricula_institucional": "X1"}
    resp = _criar(api_como, admin, outro)
    assert resp.status_code == 400
    assert "cpf" in resp.data


@pytest.mark.parametrize("senha", [None, "fraca", "semnumero!A"])
def test_senha_inicial_ausente_ou_fraca_e_recusada(api_como, admin, corpo, senha):
    dados = {**corpo}
    if senha is None:
        dados.pop("senha_inicial")
    else:
        dados["senha_inicial"] = senha
    resp = _criar(api_como, admin, dados)
    assert resp.status_code == 400
    assert "senha_inicial" in resp.data
    assert not Usuario.objects.filter(email=corpo["email"]).exists()


# ============================================================ consulta
def test_lista_mostra_contagens_e_mascara_cpf(api_como, orientador, tcc, dados_banca):
    servico_banca.cadastrar_banca(**dados_banca, usuario=orientador.usuario)

    resp = api_como(orientador.usuario).get(URL)

    assert resp.status_code == 200
    por_id = {d["id"]: d for d in resp.data}
    meu = por_id[str(orientador.pk)]
    assert meu["qtd_orientacoes"] == 1
    assert meu["qtd_bancas"] == 1
    assert meu["cpf"].startswith("***.")


def test_filtro_por_ativo_e_busca(api_como, orientador, criar_docente):
    inativo = criar_docente(ativo=False)
    cliente = api_como(orientador.usuario)

    ativos = {d["id"] for d in cliente.get(URL, {"ativo": "true"}).data}
    assert str(orientador.pk) in ativos and str(inativo.pk) not in ativos

    orientador.usuario.nome_completo = "Zuleica Andrade"
    orientador.usuario.save()
    achados = cliente.get(URL, {"busca": "zuleica"}).data
    assert [d["id"] for d in achados] == [str(orientador.pk)]


# ============================================================== edicao
def test_admin_edita_e_grava_auditoria(api_como, admin, orientador):
    resp = api_como(admin).patch(
        f"{URL}{orientador.pk}/", {"departamento": "LIC"}, format="json"
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["departamento"] == "LIC"
    assert LogAuditoria.objects.filter(
        registro_id=orientador.pk, campo="departamento", valor_novo="LIC"
    ).exists()


def test_edicao_recusa_email_de_outra_conta(api_como, admin, orientador, criar_docente):
    outro = criar_docente()
    resp = api_como(admin).patch(
        f"{URL}{orientador.pk}/", {"email": outro.usuario.email}, format="json"
    )
    assert resp.status_code == 400


def test_docente_nao_edita_cadastro(api_como, orientador):
    resp = api_como(orientador.usuario).patch(
        f"{URL}{orientador.pk}/", {"departamento": "LIC"}, format="json"
    )
    assert resp.status_code == 403


def test_desativar_e_reativar(api_como, admin, orientador):
    cliente = api_como(admin)

    resp = cliente.post(f"{URL}{orientador.pk}/desativar/")
    assert resp.status_code == 200
    assert resp.data["ativo"] is False
    orientador.usuario.refresh_from_db()
    assert orientador.usuario.ativo is False

    resp = cliente.post(f"{URL}{orientador.pk}/reativar/")
    assert resp.data["ativo"] is True


def test_desativar_id_que_nao_e_docente_da_404(api_como, admin, criar_usuario):
    secretaria = criar_usuario("SECRETARIA")
    resp = api_como(admin).post(f"{URL}{secretaria.pk}/desativar/")
    assert resp.status_code == 404
