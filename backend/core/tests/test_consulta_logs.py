"""Testes da C7 (8.3): consulta de LOG_AUDITORIA e LOG_ACESSO, so leitura e so administrador."""

from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from core.models import LogAcesso, LogAuditoria
from core.services.acesso import MAX_TENTATIVAS
from core.services.auditoria import registrar

pytestmark = pytest.mark.django_db

AUDITORIA = "/api/auditoria/"
ACESSOS = "/api/acessos/"


@pytest.fixture
def admin(criar_usuario):
    return criar_usuario("ADMINISTRADOR")


@pytest.fixture
def logs(admin, orientador, tcc):
    """Alem do log do cadastro do TCC (fixture tcc), mais duas linhas conhecidas."""
    registrar(orientador.usuario, "TCC", tcc.pk, "titulo", "Antigo", "Novo")
    registrar(admin, "DOCENTE", orientador.pk, "ativo", True, False)


def _linhas(resposta):
    return resposta.data["results"]


# ================================================================ permissao
@pytest.mark.parametrize("tipo", ["DOCENTE", "SECRETARIA", "ALUNO", "MEMBRO_EXTERNO"])
@pytest.mark.parametrize("rota", [AUDITORIA, ACESSOS])
def test_so_o_administrador_consulta_os_logs(api_como, criar_usuario, tipo, rota):
    assert api_como(criar_usuario(tipo)).get(rota).status_code == 403


@pytest.mark.parametrize("rota", [AUDITORIA, ACESSOS])
def test_anonimo_nao_consulta_os_logs(api, rota):
    assert api.get(rota).status_code in (401, 403)


@pytest.mark.parametrize("rota", [AUDITORIA, ACESSOS])
def test_logs_sao_somente_leitura_pela_api(api_como, admin, rota):
    cliente = api_como(admin)
    assert cliente.post(rota, {}, format="json").status_code == 405
    assert cliente.patch(f"{rota}{admin.pk}/", {}, format="json").status_code == 405
    assert cliente.delete(f"{rota}{admin.pk}/").status_code == 405


# ================================================================ auditoria
def test_lista_do_mais_novo_ao_mais_antigo_com_nome_do_responsavel(
    api_como, admin, orientador, logs
):
    resp = api_como(admin).get(AUDITORIA)

    assert resp.status_code == 200
    linhas = _linhas(resp)
    assert resp.data["count"] == len(linhas) == LogAuditoria.objects.count()
    datas = [linha["data_hora"] for linha in linhas]
    assert datas == sorted(datas, reverse=True)
    mudanca = next(linha for linha in linhas if linha["campo"] == "titulo")
    assert mudanca["responsavel_nome"] == orientador.usuario.nome_completo
    assert (mudanca["valor_anterior"], mudanca["valor_novo"]) == ("Antigo", "Novo")


def test_filtra_por_entidade_campo_registro_e_responsavel(
    api_como, admin, orientador, tcc, logs
):
    cliente = api_como(admin)

    por_entidade = _linhas(cliente.get(AUDITORIA, {"entidade": "docente"}))
    assert {linha["entidade"] for linha in por_entidade} == {"DOCENTE"}

    por_campo = _linhas(cliente.get(AUDITORIA, {"campo": "titulo"}))
    assert [linha["campo"] for linha in por_campo] == ["titulo"]

    por_registro = _linhas(cliente.get(AUDITORIA, {"registro": str(tcc.pk)}))
    assert por_registro
    assert {str(linha["registro_id"]) for linha in por_registro} == {str(tcc.pk)}

    por_pessoa = _linhas(cliente.get(AUDITORIA, {"responsavel": str(admin.pk)}))
    assert {str(linha["responsavel"]) for linha in por_pessoa} == {str(admin.pk)}


def test_id_mal_formado_devolve_lista_vazia_e_nao_erro(api_como, admin, logs):
    resp = api_como(admin).get(AUDITORIA, {"registro": "nao-e-uuid"})
    assert resp.status_code == 200
    assert _linhas(resp) == []


def test_filtro_de_periodo_inclui_os_dois_dias(api_como, admin, logs):
    hoje = timezone.localdate()
    ontem = hoje - timedelta(days=1)
    # LOG_AUDITORIA nao aceita UPDATE (trigger): o log antigo nasce com a data antiga
    with mock.patch(
        "django.utils.timezone.now", return_value=timezone.now() - timedelta(days=10)
    ):
        registrar(admin, "DOCENTE", admin.pk, "antigo", None, "x")
    cliente = api_como(admin)

    recentes = _linhas(cliente.get(AUDITORIA, {"de": str(ontem), "ate": str(hoje)}))
    assert "antigo" not in {linha["campo"] for linha in recentes}
    assert "titulo" in {linha["campo"] for linha in recentes}

    antigos = _linhas(cliente.get(AUDITORIA, {"ate": str(ontem)}))
    assert {linha["campo"] for linha in antigos} == {"antigo"}


def test_data_invalida_devolve_400(api_como, admin):
    resp = api_como(admin).get(AUDITORIA, {"de": "ontem"})
    assert resp.status_code == 400
    assert "de" in resp.data


def test_paginacao_limita_o_tamanho_da_resposta(api_como, admin, logs):
    total = LogAuditoria.objects.count()
    resp = api_como(admin).get(AUDITORIA, {"limit": 1})

    assert resp.data["count"] == total
    assert len(_linhas(resp)) == 1
    assert resp.data["next"] is not None


# =================================================================== acessos
def test_lista_acessos_com_nome_e_filtra_por_usuario(api_como, admin, orientador):
    LogAcesso.objects.create(usuario=orientador.usuario, ip="10.0.0.5")
    LogAcesso.objects.create(usuario=admin, ip="10.0.0.6")
    cliente = api_como(admin)

    todos = _linhas(cliente.get(ACESSOS))
    assert {linha["ip"] for linha in todos} == {"10.0.0.5", "10.0.0.6"}

    so_dele = _linhas(cliente.get(ACESSOS, {"usuario": str(orientador.usuario.pk)}))
    assert [linha["ip"] for linha in so_dele] == ["10.0.0.5"]
    assert so_dele[0]["usuario_nome"] == orientador.usuario.nome_completo


# ========================================== bloqueio de conta na auditoria
def test_bloqueio_da_conta_fica_na_auditoria(api, orientador):
    for _ in range(MAX_TENTATIVAS):
        api.post(
            "/api/auth/login/",
            {"login": orientador.usuario.email, "senha": "errada"},
            format="json",
        )

    log = LogAuditoria.objects.get(entidade="USUARIO", campo="bloqueado_ate")
    assert log.registro_id == orientador.usuario.pk
    assert log.responsavel == orientador.usuario
    assert log.valor_novo
