"""B10: fluxo completo da E1 pela API, com login JWT de verdade (sem atalhos).

Administrador cadastra pessoas e catalogo -> orientador entra, cadastra o TCC,
monta a banca e registra a defesa -> secretaria consulta sem poder alterar.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from core.models import (
    TCC,
    Banca,
    Convite,
    Curso,
    HistoricoStatus,
    LogAcesso,
    LogAuditoria,
    Usuario,
)

pytestmark = pytest.mark.django_db

SENHA = "Integra#2026"


def _entrar(api, login, senha=SENHA):
    resp = api.post("/api/auth/login/", {"login": login, "senha": senha}, format="json")
    assert resp.status_code == 200, resp.data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api


def _post(api, url, corpo, esperado=201):
    resp = api.post(url, corpo, format="json")
    assert resp.status_code == esperado, (url, resp.data)
    return resp.data


def test_fluxo_completo_da_e1(api):
    Usuario.objects.create_user(
        "admin@teste.com", SENHA, nome_completo="Admin", tipo_usuario="ADMINISTRADOR"
    )

    # 1. Administrador: catalogo e pessoas (B14, B6)
    _entrar(api, "admin@teste.com")
    area = _post(api, "/api/areas/", {"nome": "Engenharia de Software"})
    curso = Curso.objects.get(nome="ENG_COMPUTACAO")
    docentes = []
    for i, cpf in enumerate(["52998224725", "11144477735", "39053344705"]):
        docentes.append(
            _post(
                api,
                "/api/docentes/",
                {
                    "nome_completo": f"Docente {i}",
                    "email": f"docente{i}@uea.edu.br",
                    "matricula_institucional": f"MAT-{i}",
                    "cpf": cpf,
                    "departamento": "ECP",
                    "senha_inicial": SENHA,
                },
            )
        )
    externo = _post(
        api,
        "/api/usuarios/",
        {
            "nome_completo": "Dra. Externa",
            "email": "externa@ufam.edu.br",
            "tipo_usuario": "MEMBRO_EXTERNO",
            "instituicao_origem": "UFAM",
        },
    )
    _post(
        api,
        "/api/usuarios/",
        {
            "nome_completo": "Secretaria",
            "email": "secretaria@uea.edu.br",
            "tipo_usuario": "SECRETARIA",
            "senha_inicial": SENHA,
        },
    )
    aluno = _post(
        api,
        "/api/alunos/",
        {
            "nome_completo": "Aluna Teste",
            "email": "aluna@uea.edu.br",
            "matricula": "2022000001",
            "cpf": "76587434614",
            "curso": str(curso.pk),
        },
    )

    # 2. Orientador entra pela matricula e cadastra o TCC (B5, B7a)
    api.credentials()
    orientador = docentes[0]
    _entrar(api, "MAT-0")
    tcc = _post(
        api,
        "/api/tccs/",
        {
            "titulo": "Sistema de gestão de TCC",
            "area_conhecimento": area["id"],
            "modalidade": "DEFESA_EM_BANCA",
            "autor": aluno["id"],
            "orientador": orientador["id"],
            "coorientador": docentes[1]["id"],
        },
    )
    assert tcc["curso_nome"] == "ENG_COMPUTACAO"
    assert tcc["coorientador_nome"] == "Docente 1"

    # 3. Banca com membro externo (B8)
    _post(
        api,
        "/api/bancas/",
        {
            "tcc": tcc["id"],
            "titulares": [orientador["id"], docentes[1]["id"], externo["id"]],
            "suplentes": [docentes[2]["id"]],
            "data_hora": (timezone.now() + timedelta(days=10)).isoformat(),
            "tipo_local": "REMOTO",
            "local": "https://meet.exemplo.com/defesa",
        },
    )
    assert Convite.objects.filter(status="PENDENTE").count() == 3

    # 4. Defesa registrada (B7b)
    _post(
        api, f"/api/tccs/{tcc['id']}/situacao/", {"status": "APRESENTADO"}, esperado=200
    )
    detalhe = api.get(f"/api/tccs/{tcc['id']}/").data
    assert detalhe["status"] == "APRESENTADO"
    assert [h["status"] for h in detalhe["historico"]] == [
        "APRESENTADO",
        "EM_DESENVOLVIMENTO",
    ]
    assert len(detalhe["banca"]["participacoes"]) == 4

    # 5. Secretaria le tudo e nao altera nada (RBN55)
    api.credentials()
    _entrar(api, "secretaria@uea.edu.br")
    assert api.get("/api/tccs/").status_code == 200
    assert api.get(f"/api/tccs/{tcc['id']}/").status_code == 200
    assert (
        api.patch(f"/api/tccs/{tcc['id']}/", {"titulo": "X"}, format="json").status_code
        == 403
    )
    assert api.post("/api/bancas/", {}, format="json").status_code == 403

    # 6. Rastros: acessos e auditoria (RAN09)
    assert LogAcesso.objects.count() == 3
    assert (
        LogAuditoria.objects.filter(entidade="TCC", registro_id=tcc["id"]).count() == 2
    )
    assert LogAuditoria.objects.filter(entidade="BANCA").count() == 1
    assert TCC.objects.count() == 1 and Banca.objects.count() == 1
    assert HistoricoStatus.objects.count() == 2


def test_sessao_expirada_exige_novo_login(api, orientador):
    """O access vencido nao passa; o refresh ainda renova (RNF02)."""
    resp = api.post(
        "/api/auth/login/",
        {"login": orientador.usuario.email, "senha": "senha-forte-123"},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION="Bearer token-invalido")
    assert api.get("/api/tccs/").status_code == 401

    novo = api.post(
        "/api/auth/refresh/", {"refresh": resp.data["refresh"]}, format="json"
    )
    assert novo.status_code == 200
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {novo.data['access']}")
    assert api.get("/api/tccs/").status_code == 200
