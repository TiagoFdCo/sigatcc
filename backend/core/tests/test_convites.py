"""C6 (6.3): convites de banca e de audiencia (RBN49 a RBN51, RD22; PF33 a PF35, PF62).

Criterio de aceite do pacote: o convite chega completo (local ou link e
horario); o convidado aceita ou recusa.
"""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import Banca, Convite, LogAuditoria
from core.services import banca as servico_banca
from core.services import convites as servico

pytestmark = pytest.mark.django_db

URL = "/api/convites/"


@pytest.fixture
def banca(dados_banca, orientador, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        banca = servico_banca.cadastrar_banca(**dados_banca, usuario=orientador.usuario)
    return banca


def _convite_de(banca, docente):
    return Convite.objects.get(banca=banca, usuario=docente.usuario)


def _assinatura_no_email(mensagem):
    linha = next(x for x in mensagem.body.splitlines() if "/convites/responder" in x)
    return parse_qs(urlparse(linha.strip()).query)["c"][0]


# ---------------------------------------------- envio no cadastro da banca
def test_cadastro_da_banca_envia_um_email_por_convite(banca, outros_docentes):
    # 2 titulares + 1 suplente; o orientador cadastrou e nao recebe convite
    destinatarios = sorted(m.to[0] for m in mail.outbox)
    esperados = sorted(d.usuario.email for d in outros_docentes[:3])
    assert destinatarios == esperados


def test_convite_chega_completo(banca, outros_docentes):
    mensagem = next(
        m for m in mail.outbox if m.to == [outros_docentes[0].usuario.email]
    )
    inicio = timezone.localtime(banca.data_hora_inicio)
    fim = timezone.localtime(banca.data_hora_fim)
    assert banca.tcc.titulo in mensagem.subject
    assert "como titular" in mensagem.body
    assert "Presencial: bloco NUCOMP, sala 10" in mensagem.body
    assert f"das {inicio:%H:%M} às {fim:%H:%M}" in mensagem.body
    assert "/convites/responder?c=" in mensagem.body


def test_suplente_e_convidado_como_suplente(banca, outros_docentes):
    mensagem = next(
        m for m in mail.outbox if m.to == [outros_docentes[2].usuario.email]
    )
    assert "como suplente" in mensagem.body


def test_banca_remota_leva_o_link(
    dados_banca, orientador, django_capture_on_commit_callbacks
):
    dados = {
        **dados_banca,
        "tipo_local": "REMOTO",
        "link_remoto": "https://meet.exemplo.com/defesa",
    }
    with django_capture_on_commit_callbacks(execute=True):
        servico_banca.cadastrar_banca(**dados, usuario=orientador.usuario)
    assert "Remota: https://meet.exemplo.com/defesa" in mail.outbox[0].body


def test_banca_recusada_nao_envia_nada(
    dados_banca, orientador, django_capture_on_commit_callbacks
):
    dados = {**dados_banca, "data_hora_inicio": timezone.now() - timedelta(days=1)}
    with (
        django_capture_on_commit_callbacks(execute=True),
        pytest.raises(ValidationError),
    ):
        servico_banca.cadastrar_banca(**dados, usuario=orientador.usuario)
    assert mail.outbox == []


# ------------------------------------------------- resposta pela tela (PF35)
def test_convidado_lista_e_aceita(api_como, banca, outros_docentes):
    cliente = api_como(outros_docentes[0].usuario)
    lista = cliente.get(URL).data
    assert len(lista) == 1
    assert lista[0]["papel"] == "TITULAR"
    assert lista[0]["banca"]["bloco"] == "NUCOMP"
    resp = cliente.post(f"{URL}{lista[0]['id']}/responder/", {"resposta": "ACEITO"})
    assert resp.status_code == 200, resp.data
    assert resp.data["status"] == "ACEITO" and resp.data["respondido_em"]
    convite = _convite_de(banca, outros_docentes[0])
    assert LogAuditoria.objects.filter(
        entidade="CONVITE", registro_id=convite.pk, valor_novo="ACEITO"
    ).exists()


def test_responde_uma_vez_so(api_como, banca, outros_docentes):
    convite = _convite_de(banca, outros_docentes[0])
    cliente = api_como(outros_docentes[0].usuario)
    cliente.post(f"{URL}{convite.pk}/responder/", {"resposta": "RECUSADO"})
    resp = cliente.post(f"{URL}{convite.pk}/responder/", {"resposta": "ACEITO"})
    assert resp.status_code == 400


def test_outro_usuario_nao_responde(api_como, banca, outros_docentes):
    convite = _convite_de(banca, outros_docentes[0])
    resp = api_como(outros_docentes[1].usuario).post(
        f"{URL}{convite.pk}/responder/", {"resposta": "ACEITO"}
    )
    assert resp.status_code == 403


def test_nao_responde_depois_da_defesa(api_como, banca, outros_docentes):
    Banca.objects.filter(pk=banca.pk).update(
        data_hora_inicio=timezone.now() - timedelta(hours=1)
    )
    convite = _convite_de(banca, outros_docentes[0])
    resp = api_como(outros_docentes[0].usuario).post(
        f"{URL}{convite.pk}/responder/", {"resposta": "ACEITO"}
    )
    assert resp.status_code == 400


# ------------------------------------------- resposta pelo link (sem login)
def test_link_do_email_mostra_e_responde_sem_login(api, banca, outros_docentes):
    mensagem = next(
        m for m in mail.outbox if m.to == [outros_docentes[1].usuario.email]
    )
    c = _assinatura_no_email(mensagem)
    resumo = api.get(f"{URL}link/", {"c": c})
    assert resumo.status_code == 200
    assert resumo.data["tcc_titulo"] == banca.tcc.titulo
    assert "email" not in resumo.data
    resp = api.post(f"{URL}link/", {"c": c, "resposta": "RECUSADO"}, format="json")
    assert resp.status_code == 200, resp.data
    assert _convite_de(banca, outros_docentes[1]).status == "RECUSADO"


@pytest.mark.parametrize("c", ["", "abc", "123:falso:assinatura"])
def test_link_adulterado_e_recusado(api, banca, c):
    assert api.get(f"{URL}link/", {"c": c}).status_code == 400


def test_link_funciona_mesmo_com_token_vencido_no_navegador(
    api, banca, outros_docentes
):
    api.credentials(HTTP_AUTHORIZATION="Bearer token-vencido")
    c = servico.assinatura(_convite_de(banca, outros_docentes[0]))
    assert api.get(f"{URL}link/", {"c": c}).status_code == 200


# ------------------------------------------------------------ reenvio (PF33)
def test_orientador_reenvia_convite_pendente(
    api_como, banca, orientador, outros_docentes, django_capture_on_commit_callbacks
):
    convite = _convite_de(banca, outros_docentes[0])
    antes = convite.enviado_em
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        resp = api_como(orientador.usuario).post(f"{URL}{convite.pk}/reenviar/")
    assert resp.status_code == 200, resp.data
    convite.refresh_from_db()
    assert convite.enviado_em > antes
    assert [m.to for m in mail.outbox] == [[outros_docentes[0].usuario.email]]


def test_quem_nao_edita_o_tcc_nao_reenvia(api_como, banca, outros_docentes):
    convite = _convite_de(banca, outros_docentes[0])
    resp = api_como(outros_docentes[1].usuario).post(f"{URL}{convite.pk}/reenviar/")
    assert resp.status_code == 403


def test_convite_respondido_nao_e_reenviado(banca, orientador, outros_docentes):
    convite = _convite_de(banca, outros_docentes[0])
    servico.responder_convite(convite_id=convite.pk, resposta="ACEITO")
    with pytest.raises(ValidationError, match="pendente"):
        servico.reenviar_convite(convite_id=convite.pk, usuario=orientador.usuario)


# --------------------------------------------------------- audiencia (PF34)
def test_convite_de_audiencia_por_pessoa(
    api_como,
    banca,
    orientador,
    criar_aluno,
    outros_docentes,
    django_capture_on_commit_callbacks,
):
    aluno = criar_aluno()
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        resp = api_como(orientador.usuario).post(
            f"/api/bancas/{banca.pk}/audiencia/",
            {"usuarios": [str(aluno.pk), str(outros_docentes[3].pk)]},
            format="json",
        )
    assert resp.status_code == 201, resp.data
    audiencia = [c for c in resp.data["convites"] if c["tipo"] == "AUDIENCIA"]
    assert len(audiencia) == 2
    assert len(mail.outbox) == 2
    assert "assistir à defesa" in mail.outbox[0].body


def test_membro_autor_e_repetido_nao_sao_convidados_para_audiencia(
    banca, orientador, outros_docentes, criar_aluno
):
    for pessoa in (outros_docentes[0].usuario, banca.tcc.autor.usuario):
        with pytest.raises(ValidationError, match="já participa"):
            servico.convidar_audiencia(
                banca=banca, usuarios=[pessoa], usuario=orientador.usuario
            )
    aluno = criar_aluno()
    servico.convidar_audiencia(
        banca=banca, usuarios=[aluno.usuario], usuario=orientador.usuario
    )
    with pytest.raises(ValidationError, match="já foi convidado"):
        servico.convidar_audiencia(
            banca=banca, usuarios=[aluno.usuario], usuario=orientador.usuario
        )


def test_externo_nao_e_convidado_para_audiencia(banca, orientador, membro_externo):
    with pytest.raises(ValidationError, match="não pode ser convidado"):
        servico.convidar_audiencia(
            banca=banca, usuarios=[membro_externo.usuario], usuario=orientador.usuario
        )


def test_membro_da_banca_que_nao_edita_nao_convida_audiencia(
    api_como, banca, outros_docentes, criar_aluno
):
    resp = api_como(outros_docentes[0].usuario).post(
        f"/api/bancas/{banca.pk}/audiencia/",
        {"usuarios": [str(criar_aluno().pk)]},
        format="json",
    )
    assert resp.status_code == 403


def test_convidado_de_audiencia_aceita_pela_tela(
    api_como, banca, orientador, criar_aluno
):
    aluno = criar_aluno()
    (convite,) = servico.convidar_audiencia(
        banca=banca, usuarios=[aluno.usuario], usuario=orientador.usuario
    )
    resp = api_como(aluno.usuario).post(
        f"{URL}{convite.pk}/responder/", {"resposta": "ACEITO"}
    )
    assert resp.status_code == 200
    assert resp.data["papel"] is None
