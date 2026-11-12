"""Testes da C2a (perfil e acesso do aluno)."""

from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from core.models import TCC, Aluno, AreaConhecimento, LogAuditoria
from core.services import perfil_aluno as servico_perfil
from core.services import pessoas as servico_pessoas

pytestmark = pytest.mark.django_db

SENHA = "Aluno#2026x"
SENHA_ANTIGA = "senha-forte-123"  # a que o conftest usa em criar_usuario
URL_PERFIL = "/api/alunos/meu-perfil/"
LOGIN = "/api/auth/login/"


@pytest.fixture
def admin(criar_usuario):
    return criar_usuario("ADMINISTRADOR")


@pytest.fixture
def aluno_sem_senha(aluno):
    aluno.usuario.set_unusable_password()
    aluno.usuario.save(update_fields=["password"])
    return aluno


@pytest.fixture
def areas(db):
    return [
        AreaConhecimento.objects.create(nome="Inteligência Artificial"),
        AreaConhecimento.objects.create(nome="Redes de Computadores"),
        AreaConhecimento.objects.create(nome="Informática na Educação"),
    ]


def _url_senha(aluno):
    return f"/api/alunos/{aluno.pk}/senha/"


def _logs(aluno, campo):
    return LogAuditoria.objects.filter(
        entidade="ALUNO", registro_id=aluno.pk, campo=campo
    ).order_by("data_hora")


# ===================================== senha definida pelo administrador
def test_admin_define_a_senha_e_o_aluno_entra(api_como, api, admin, aluno_sem_senha):
    resp = api_como(admin).post(
        _url_senha(aluno_sem_senha), {"senha": SENHA}, format="json"
    )

    assert resp.status_code == 200, resp.data
    assert "senha" not in resp.data
    assert SENHA not in str(resp.data)

    api.force_authenticate(user=None)
    entrada = api.post(
        LOGIN,
        {"login": aluno_sem_senha.usuario.email, "senha": SENHA},
        format="json",
    )
    assert entrada.status_code == 200, entrada.data
    assert entrada.data["usuario"]["tipo_usuario"] == "ALUNO"


def test_redefinir_troca_a_senha_e_zera_o_bloqueio(api_como, api, admin, aluno):
    conta = aluno.usuario
    conta.tentativas_falhas = 3
    conta.bloqueado_ate = timezone.now() + timedelta(minutes=10)
    conta.save(update_fields=["tentativas_falhas", "bloqueado_ate"])

    resp = api_como(admin).post(_url_senha(aluno), {"senha": SENHA}, format="json")

    assert resp.status_code == 200, resp.data
    conta.refresh_from_db()
    assert conta.tentativas_falhas == 0
    assert conta.bloqueado_ate is None

    api.force_authenticate(user=None)
    nova = api.post(LOGIN, {"login": conta.email, "senha": SENHA}, format="json")
    antiga = api.post(
        LOGIN, {"login": conta.email, "senha": SENHA_ANTIGA}, format="json"
    )
    assert nova.status_code == 200
    assert antiga.status_code == 401


@pytest.mark.parametrize(
    "fraca",
    ["abc", "12345678", "semmaiuscula1#", "SemNumero#abc", "SemEspecial123"],
)
def test_senha_fraca_e_recusada(api_como, admin, aluno, fraca):
    resp = api_como(admin).post(_url_senha(aluno), {"senha": fraca}, format="json")

    assert resp.status_code == 400
    assert "senha" in resp.data
    aluno.usuario.refresh_from_db()
    assert aluno.usuario.check_password(SENHA_ANTIGA)
    assert not _logs(aluno, "senha").exists()


def test_senha_em_branco_e_recusada(api_como, admin, aluno):
    resp = api_como(admin).post(_url_senha(aluno), {"senha": ""}, format="json")
    assert resp.status_code == 400
    assert "senha" in resp.data


def test_log_registra_a_senha_sem_guarda_la(api_como, admin, aluno_sem_senha):
    cliente = api_como(admin)
    cliente.post(_url_senha(aluno_sem_senha), {"senha": SENHA}, format="json")
    cliente.post(_url_senha(aluno_sem_senha), {"senha": "Outra#2026ab"}, format="json")

    primeiro, segundo = _logs(aluno_sem_senha, "senha")
    assert (primeiro.valor_anterior, primeiro.valor_novo) == (None, "definida")
    assert (segundo.valor_anterior, segundo.valor_novo) == ("definida", "redefinida")
    assert primeiro.responsavel == admin
    for linha in (primeiro, segundo):
        assert SENHA not in f"{linha.valor_anterior}{linha.valor_novo}"
        assert "Outra#2026ab" not in f"{linha.valor_anterior}{linha.valor_novo}"


def test_so_o_administrador_define_senha(api_como, criar_usuario, orientador, aluno):
    for quem in (orientador.usuario, aluno.usuario, criar_usuario("SECRETARIA")):
        resp = api_como(quem).post(_url_senha(aluno), {"senha": SENHA}, format="json")
        assert resp.status_code == 403
    aluno.usuario.refresh_from_db()
    assert aluno.usuario.check_password(SENHA_ANTIGA)


def test_definir_senha_sem_login_devolve_401(api, aluno):
    resp = api.post(_url_senha(aluno), {"senha": SENHA}, format="json")
    assert resp.status_code == 401


def test_aluno_inativo_nao_recebe_senha(api_como, admin, aluno):
    aluno.usuario.ativo = False
    aluno.usuario.save(update_fields=["ativo"])

    resp = api_como(admin).post(_url_senha(aluno), {"senha": SENHA}, format="json")

    assert resp.status_code == 400
    assert "aluno" in resp.data


def test_aluno_inexistente_da_404(api_como, admin):
    resp = api_como(admin).post(
        "/api/alunos/00000000-0000-0000-0000-000000000000/senha/",
        {"senha": SENHA},
        format="json",
    )
    assert resp.status_code == 404


def test_falha_na_auditoria_desfaz_a_senha(admin, aluno):
    with (
        mock.patch(
            "core.services.pessoas.registrar", side_effect=RuntimeError("log fora")
        ),
        pytest.raises(RuntimeError),
    ):
        servico_pessoas.definir_senha_aluno(
            aluno_id=aluno.pk, senha=SENHA, usuario=admin
        )
    aluno.usuario.refresh_from_db()
    assert aluno.usuario.check_password(SENHA_ANTIGA)


# ============================================================ meu perfil
def test_aluno_ve_o_proprio_perfil(api_como, aluno):
    resp = api_como(aluno.usuario).get(URL_PERFIL)

    assert resp.status_code == 200, resp.data
    assert resp.data["id"] == str(aluno.pk)
    assert resp.data["email"] == aluno.usuario.email
    assert resp.data["matricula"] == aluno.matricula
    assert resp.data["curso_nome"] == aluno.curso.nome
    assert resp.data["cadastro_confirmado"] is False
    assert resp.data["areas_interesse"] == []
    assert resp.data["meu_tcc"] is None
    assert resp.data["cpf"].startswith("***.") and resp.data["cpf"].endswith("-**")
    assert aluno.cpf not in str(resp.data)


def test_perfil_traz_o_tcc_do_aluno(api_como, aluno, tcc):
    resp = api_como(aluno.usuario).get(URL_PERFIL)

    assert resp.data["meu_tcc"]["id"] == str(tcc.pk)
    assert resp.data["meu_tcc"]["titulo"] == tcc.titulo
    assert resp.data["meu_tcc"]["status"] == "EM_DESENVOLVIMENTO"


def test_perfil_ignora_tcc_inativo(api_como, aluno, tcc):
    TCC.objects.filter(pk=tcc.pk).update(
        ativo=False,
        motivo_inativacao="Cadastro duplicado",  # RD13: inativar exige motivo
    )
    assert api_como(aluno.usuario).get(URL_PERFIL).data["meu_tcc"] is None


def test_perfil_nao_mostra_tcc_de_outro_aluno(api_como, criar_aluno, tcc):
    outro = criar_aluno()
    assert api_como(outro.usuario).get(URL_PERFIL).data["meu_tcc"] is None


def test_aluno_escolhe_areas_de_interesse(api_como, aluno, areas):
    ids = [str(areas[0].pk), str(areas[1].pk)]

    resp = api_como(aluno.usuario).patch(
        URL_PERFIL, {"areas_interesse": ids}, format="json"
    )

    assert resp.status_code == 200, resp.data
    assert {a["nome"] for a in resp.data["areas_interesse"]} == {
        areas[0].nome,
        areas[1].nome,
    }
    assert set(aluno.areas_interesse.values_list("pk", flat=True)) == {
        areas[0].pk,
        areas[1].pk,
    }
    (log,) = _logs(aluno, "areas_interesse")
    assert log.responsavel == aluno.usuario
    assert log.valor_anterior is None
    assert set(log.valor_novo.split(",")) == set(ids)


def test_mudar_as_areas_grava_o_antes_e_o_depois(api_como, aluno, areas):
    cliente = api_como(aluno.usuario)
    cliente.patch(URL_PERFIL, {"areas_interesse": [str(areas[0].pk)]}, format="json")
    cliente.patch(URL_PERFIL, {"areas_interesse": [str(areas[2].pk)]}, format="json")

    _, segundo = _logs(aluno, "areas_interesse")
    assert segundo.valor_anterior == str(areas[0].pk)
    assert segundo.valor_novo == str(areas[2].pk)
    assert list(aluno.areas_interesse.all()) == [areas[2]]


def test_repetir_as_mesmas_areas_nao_grava_log(api_como, aluno, areas):
    cliente = api_como(aluno.usuario)
    corpo = {"areas_interesse": [str(areas[0].pk), str(areas[1].pk)]}
    cliente.patch(URL_PERFIL, corpo, format="json")
    cliente.patch(URL_PERFIL, corpo, format="json")
    assert _logs(aluno, "areas_interesse").count() == 1


def test_lista_vazia_limpa_as_areas(api_como, aluno, areas):
    cliente = api_como(aluno.usuario)
    cliente.patch(URL_PERFIL, {"areas_interesse": [str(areas[0].pk)]}, format="json")

    resp = cliente.patch(URL_PERFIL, {"areas_interesse": []}, format="json")

    assert resp.status_code == 200
    assert resp.data["areas_interesse"] == []
    assert _logs(aluno, "areas_interesse").last().valor_novo is None


def test_area_repetida_conta_uma_vez(api_como, aluno, areas):
    id_area = str(areas[0].pk)
    resp = api_como(aluno.usuario).patch(
        URL_PERFIL, {"areas_interesse": [id_area, id_area]}, format="json"
    )
    assert resp.status_code == 200
    assert aluno.areas_interesse.count() == 1


def test_area_inexistente_e_recusada(api_como, aluno, areas):
    resp = api_como(aluno.usuario).patch(
        URL_PERFIL,
        {"areas_interesse": ["00000000-0000-0000-0000-000000000000"]},
        format="json",
    )
    assert resp.status_code == 400
    assert "areas_interesse" in resp.data
    assert aluno.areas_interesse.count() == 0


def test_patch_sem_areas_e_recusado(api_como, aluno):
    resp = api_como(aluno.usuario).patch(URL_PERFIL, {}, format="json")
    assert resp.status_code == 400
    assert "areas_interesse" in resp.data


def test_aluno_nao_altera_outros_dados_pelo_perfil(api_como, aluno, areas):
    matricula, cpf = aluno.matricula, aluno.cpf

    api_como(aluno.usuario).patch(
        URL_PERFIL,
        {
            "areas_interesse": [str(areas[0].pk)],
            "matricula": "999",
            "cpf": "00000000000",
            "cadastro_confirmado": True,
            "nome_completo": "Outro Nome",
        },
        format="json",
    )

    aluno = Aluno.objects.get(pk=aluno.pk)
    assert (aluno.matricula, aluno.cpf) == (matricula, cpf)
    assert aluno.cadastro_confirmado is False
    assert aluno.usuario.nome_completo != "Outro Nome"


def test_falha_na_auditoria_desfaz_as_areas(aluno, areas):
    with (
        mock.patch(
            "core.services.perfil_aluno.registrar", side_effect=RuntimeError("log fora")
        ),
        pytest.raises(RuntimeError),
    ):
        servico_perfil.atualizar_areas_interesse(
            aluno=aluno, areas=[areas[0]], usuario=aluno.usuario
        )
    assert aluno.areas_interesse.count() == 0


def test_so_aluno_usa_o_meu_perfil(api_como, orientador, criar_usuario):
    for quem in (
        orientador.usuario,
        criar_usuario("ADMINISTRADOR"),
        criar_usuario("SECRETARIA"),
    ):
        cliente = api_como(quem)
        assert cliente.get(URL_PERFIL).status_code == 403
        assert (
            cliente.patch(
                URL_PERFIL, {"areas_interesse": []}, format="json"
            ).status_code
            == 403
        )


def test_meu_perfil_sem_login_devolve_401(api):
    assert api.get(URL_PERFIL).status_code == 401


def test_a_rota_meu_perfil_nao_e_confundida_com_um_id(api_como, aluno):
    """/alunos/meu-perfil/ nao pode cair na rota de detalhe /alunos/{id}/."""
    assert api_como(aluno.usuario).get(URL_PERFIL).status_code == 200
