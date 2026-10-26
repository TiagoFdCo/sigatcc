"""Testes do B14 (alunos, secretaria, administrador, membro externo e catalogos)."""

import pytest

from core.models import Aluno, AreaConhecimento, Curso, MembroExterno, Usuario

pytestmark = pytest.mark.django_db

CPF_VALIDO = "529.982.247-25"
SENHA = "Inicial#2026"


@pytest.fixture
def admin(criar_usuario):
    return criar_usuario("ADMINISTRADOR")


@pytest.fixture
def corpo_aluno():
    return {
        "nome_completo": "Rafaela Duarte",
        "email": "rafaela@uea.edu.br",
        "matricula": "2022009999",
        "cpf": CPF_VALIDO,
        "curso": str(Curso.objects.get(nome="SISTEMAS_INFORMACAO").pk),
    }


# ================================================================ alunos
def test_admin_cadastra_aluno_sem_senha(api_como, admin, corpo_aluno):
    resp = api_como(admin).post("/api/alunos/", corpo_aluno, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["cpf"] == "***.982.247-**"
    assert str(resp.data["curso"]) == corpo_aluno["curso"]
    aluno = Aluno.objects.get(matricula="2022009999")
    assert aluno.usuario.tipo_usuario == "ALUNO"
    assert not aluno.usuario.has_usable_password()


def test_aluno_cadastrado_pode_ser_autor_de_tcc(
    api_como, admin, orientador, area, corpo_aluno
):
    aluno_id = (
        api_como(admin).post("/api/alunos/", corpo_aluno, format="json").data["id"]
    )
    corpo_tcc = {
        "titulo": "Um TCC",
        "area_conhecimento": str(area.pk),
        "modalidade": "DEFESA_EM_BANCA",
        "autor": aluno_id,
        "orientador": str(orientador.pk),
    }
    resp = api_como(orientador.usuario).post("/api/tccs/", corpo_tcc, format="json")
    assert resp.status_code == 201, resp.data


def test_matricula_de_aluno_repetida_e_recusada(api_como, admin, corpo_aluno):
    cliente = api_como(admin)
    cliente.post("/api/alunos/", corpo_aluno, format="json")
    outro = {**corpo_aluno, "email": "outro@uea.edu.br", "cpf": "111.444.777-35"}
    resp = cliente.post("/api/alunos/", outro, format="json")
    assert resp.status_code == 400
    assert "matricula" in resp.data


def test_cpf_nao_repete_entre_aluno_e_docente(api_como, admin, corpo_aluno):
    cliente = api_como(admin)
    cliente.post("/api/alunos/", corpo_aluno, format="json")
    docente = {
        "nome_completo": "Outra Pessoa",
        "email": "outra@uea.edu.br",
        "matricula_institucional": "INST-1",
        "cpf": CPF_VALIDO,
        "departamento": "SI",
        "senha_inicial": SENHA,
    }
    resp = cliente.post("/api/docentes/", docente, format="json")
    assert resp.status_code == 400
    assert "cpf" in resp.data


def test_docente_consulta_alunos_mas_nao_cadastra(
    api_como, orientador, aluno, corpo_aluno
):
    cliente = api_como(orientador.usuario)
    assert cliente.get("/api/alunos/").status_code == 200
    assert cliente.post("/api/alunos/", corpo_aluno, format="json").status_code == 403


def test_aluno_nao_ve_lista_de_alunos(api_como, aluno):
    assert api_como(aluno.usuario).get("/api/alunos/").status_code == 403


def test_admin_edita_curso_do_aluno(api_como, admin, aluno):
    lic = Curso.objects.get(nome="LICENCIATURA_COMPUTACAO")
    resp = api_como(admin).patch(
        f"/api/alunos/{aluno.pk}/", {"curso": str(lic.pk)}, format="json"
    )
    assert resp.status_code == 200, resp.data
    aluno.refresh_from_db()
    assert aluno.curso == lic


# ============================================ secretaria, admin e externo
def test_admin_cadastra_secretaria_que_consegue_entrar(api_como, api, admin):
    corpo = {
        "nome_completo": "Sandra Melo",
        "email": "secretaria@uea.edu.br",
        "tipo_usuario": "SECRETARIA",
        "senha_inicial": SENHA,
    }
    resp = api_como(admin).post("/api/usuarios/", corpo, format="json")
    assert resp.status_code == 201, resp.data

    api.force_authenticate(user=None)
    login = api.post(
        "/api/auth/login/",
        {"login": "secretaria@uea.edu.br", "senha": SENHA},
        format="json",
    )
    assert login.status_code == 200


def test_secretaria_exige_senha(api_como, admin):
    corpo = {
        "nome_completo": "X",
        "email": "x@uea.edu.br",
        "tipo_usuario": "SECRETARIA",
    }
    resp = api_como(admin).post("/api/usuarios/", corpo, format="json")
    assert resp.status_code == 400
    assert "senha_inicial" in resp.data


def test_membro_externo_exige_instituicao_e_fica_sem_senha(api_como, admin):
    cliente = api_como(admin)
    corpo = {
        "nome_completo": "Dra. Externa",
        "email": "ext@ufam.edu.br",
        "tipo_usuario": "MEMBRO_EXTERNO",
    }

    assert cliente.post("/api/usuarios/", corpo, format="json").status_code == 400

    resp = cliente.post(
        "/api/usuarios/", {**corpo, "instituicao_origem": "UFAM"}, format="json"
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["instituicao_origem"] == "UFAM"
    conta = Usuario.objects.get(email="ext@ufam.edu.br")
    assert MembroExterno.objects.filter(usuario=conta).exists()
    assert not conta.has_usable_password()


@pytest.mark.parametrize("tipo", ["DOCENTE", "ALUNO"])
def test_usuarios_nao_cadastra_docente_nem_aluno(api_como, admin, tipo):
    corpo = {
        "nome_completo": "X",
        "email": "x@uea.edu.br",
        "tipo_usuario": tipo,
        "senha_inicial": SENHA,
    }
    resp = api_como(admin).post("/api/usuarios/", corpo, format="json")
    assert resp.status_code == 400
    assert "tipo_usuario" in resp.data


def test_docente_lista_membros_externos(api_como, orientador, membro_externo):
    resp = api_como(orientador.usuario).get(
        "/api/usuarios/", {"tipo": "MEMBRO_EXTERNO"}
    )
    assert resp.status_code == 200
    assert [u["id"] for u in resp.data] == [str(membro_externo.pk)]


def test_admin_nao_desativa_a_propria_conta(api_como, admin):
    resp = api_como(admin).post(f"/api/usuarios/{admin.pk}/desativar/")
    assert resp.status_code == 400
    admin.refresh_from_db()
    assert admin.ativo is True


def test_desativar_secretaria(api_como, admin, criar_usuario):
    secretaria = criar_usuario("SECRETARIA")
    resp = api_como(admin).post(f"/api/usuarios/{secretaria.pk}/desativar/")
    assert resp.status_code == 200
    assert resp.data["ativo"] is False


# ============================================================ catalogos
def test_lista_os_tres_cursos(api_como, orientador):
    resp = api_como(orientador.usuario).get("/api/cursos/")
    assert resp.status_code == 200
    assert len(resp.data) == 3


def test_admin_cadastra_area_sem_repetir(api_como, admin):
    cliente = api_como(admin)
    assert (
        cliente.post("/api/areas/", {"nome": "Robótica"}, format="json").status_code
        == 201
    )
    repetida = cliente.post("/api/areas/", {"nome": "robótica"}, format="json")
    assert repetida.status_code == 400
    assert AreaConhecimento.objects.filter(nome__iexact="robótica").count() == 1


def test_docente_lista_areas_mas_nao_cadastra(api_como, orientador, area):
    cliente = api_como(orientador.usuario)
    assert len(cliente.get("/api/areas/").data) == 1
    assert (
        cliente.post("/api/areas/", {"nome": "Nova"}, format="json").status_code == 403
    )
