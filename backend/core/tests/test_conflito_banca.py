from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import Banca, ParticipacaoBanca, TipoLocal
from core.services.banca import validar_conflito_banca


@pytest.fixture
def cenario_banca(tcc, orientador):
    """TCC base e o orientador dele (fixtures do conftest)."""
    return tcc, orientador, orientador.usuario


@pytest.mark.django_db
def test_conflito_membro_sobreposicao(cenario_banca):
    """Verifica bloqueio quando um mesmo membro tem bancas com horários sobrepostos."""
    tcc, _docente, user_docente = cenario_banca
    inicio_existente = timezone.now() + timedelta(days=5)

    # Cria banca 1 (das 14h às 16h)
    banca1 = Banca.objects.create(
        tcc=tcc,
        data_hora_inicio=inicio_existente,
        tipo_local=TipoLocal.PRESENCIAL,
        bloco="A",
        sala="101",
    )
    ParticipacaoBanca.objects.create(
        banca=banca1, usuario=user_docente, tipo_membro="TITULAR"
    )

    # Tenta validar banca 2 sobreposta (iniciando 1h depois com o mesmo docente)
    inicio_sobreposto = inicio_existente + timedelta(hours=1)
    with pytest.raises(ValidationError):
        validar_conflito_banca(
            data_hora_inicio=inicio_sobreposto,
            tipo_local=TipoLocal.PRESENCIAL,
            bloco="B",
            sala="202",
            usuarios_membros_ids=[user_docente.id],
        )


@pytest.mark.django_db
def test_conflito_local_presencial(cenario_banca):
    """Verifica bloqueio quando duas bancas compartilham a mesma sala e bloco no mesmo horário."""
    tcc, _docente, _user_docente = cenario_banca
    inicio_existente = timezone.now() + timedelta(days=5)

    Banca.objects.create(
        tcc=tcc,
        data_hora_inicio=inicio_existente,
        tipo_local=TipoLocal.PRESENCIAL,
        bloco="A",
        sala="101",
    )

    inicio_sobreposto = inicio_existente + timedelta(minutes=30)
    with pytest.raises(ValidationError):
        validar_conflito_banca(
            data_hora_inicio=inicio_sobreposto,
            tipo_local=TipoLocal.PRESENCIAL,
            bloco="A",
            sala="101",
        )


@pytest.mark.django_db
def test_bancas_encostadas_sem_conflito(cenario_banca):
    """Garante que bancas seguidas (ex: 14h-16h e 16h-18h) não gerem falso positivo de conflito."""
    tcc, _docente, user_docente = cenario_banca
    inicio_existente = timezone.now() + timedelta(days=5)

    banca1 = Banca.objects.create(
        tcc=tcc,
        data_hora_inicio=inicio_existente,
        tipo_local=TipoLocal.PRESENCIAL,
        bloco="A",
        sala="101",
    )
    ParticipacaoBanca.objects.create(
        banca=banca1, usuario=user_docente, tipo_membro="TITULAR"
    )

    # Banca 2 inicia exatamente quando a Banca 1 termina (2h depois)
    inicio_encostado = inicio_existente + timedelta(hours=2)

    # Não deve lançar exceção
    validar_conflito_banca(
        data_hora_inicio=inicio_encostado,
        tipo_local=TipoLocal.PRESENCIAL,
        bloco="A",
        sala="101",
        usuarios_membros_ids=[user_docente.id],
    )


# ------------------------------------------------------------------------
# Casos do Plano de Testes (C13, cap. 8): CT-BAN-01 a 03 pelo fluxo completo
# de cadastro de banca (servico cadastrar_banca), nao so pela validacao.
# ------------------------------------------------------------------------
@pytest.fixture
def novo_tcc(criar_aluno, orientador, area):
    """Cada banca precisa de um TCC proprio (uma banca por TCC)."""
    from core.services import tcc as servico_tcc

    def _criar():
        return servico_tcc.cadastrar_tcc(
            dados={
                "titulo": "TCC para teste de conflito",
                "area_conhecimento": area,
                "modalidade": "DEFESA_EM_BANCA",
                "autor": criar_aluno(),
                "orientador": orientador,
            },
            usuario=orientador.usuario,
        )

    return _criar


@pytest.fixture
def as_14h():
    """Daqui a 10 dias, as 14h (hora local)."""
    dia = timezone.localtime() + timedelta(days=10)
    return dia.replace(hour=14, minute=0, second=0, microsecond=0)


def _cadastrar(tcc, membros, inicio, **local):
    from core.services import banca as servico_banca

    local = local or {"tipo_local": "PRESENCIAL", "bloco": "NUCOMP", "sala": "10"}
    return servico_banca.cadastrar_banca(
        tcc=tcc,
        titulares=[tcc.orientador.usuario, *membros],
        data_hora_inicio=inicio,
        usuario=tcc.orientador.usuario,
        **local,
    )


def _sala(numero):
    return {"tipo_local": "PRESENCIAL", "bloco": "NUCOMP", "sala": str(numero)}


def test_ct_ban_01_membro_em_comum_antes_e_depois(novo_tcc, outros_docentes, as_14h):
    """CT-BAN-01: banca X 14h-16h; Y as 15h e Z as 13h com o mesmo titular sao recusadas."""
    d1, d2, d3, _ = (d.usuario for d in outros_docentes)
    _cadastrar(novo_tcc(), [d1, d2], as_14h, **_sala(1))
    total = Banca.objects.count()

    for inicio, sala in (
        (as_14h + timedelta(hours=1), 2),
        (as_14h - timedelta(hours=1), 3),
    ):
        with pytest.raises(ValidationError) as erro:
            _cadastrar(novo_tcc(), [d1, d3], inicio, **_sala(sala))
        assert "membros" in erro.value.detail
    assert Banca.objects.count() == total  # nada gravado


def test_ct_ban_02_mesma_sala_recusa_e_remota_aceita(
    criar_docente, criar_aluno, area, as_14h
):
    """CT-BAN-02: sem membros em comum, mesma sala e recusada; remota no mesmo horario e aceita."""
    from core.services import tcc as servico_tcc

    def tcc_de_outro_orientador():
        orientador = criar_docente()
        tcc = servico_tcc.cadastrar_tcc(
            dados={
                "titulo": "TCC de outro orientador",
                "area_conhecimento": area,
                "modalidade": "DEFESA_EM_BANCA",
                "autor": criar_aluno(),
                "orientador": orientador,
            },
            usuario=orientador.usuario,
        )
        return tcc, [criar_docente().usuario, criar_docente().usuario]

    tcc_x, membros_x = tcc_de_outro_orientador()
    _cadastrar(tcc_x, membros_x, as_14h, **_sala(10))

    tcc_y, membros_y = tcc_de_outro_orientador()
    with pytest.raises(ValidationError) as erro:
        _cadastrar(tcc_y, membros_y, as_14h + timedelta(hours=1), **_sala(10))
    assert "local" in erro.value.detail

    tcc_z, membros_z = tcc_de_outro_orientador()
    remota = {"tipo_local": "REMOTO", "link_remoto": "https://meet.example.org/z"}
    assert _cadastrar(tcc_z, membros_z, as_14h + timedelta(hours=1), **remota)


def test_ct_ban_03_valor_limite_16h00_aceita_15h59_recusa(
    novo_tcc, outros_docentes, as_14h
):
    """CT-BAN-03: com X das 14h as 16h, Y as 16h00 e aceita e Z as 15h59 e recusada."""
    d1, d2, d3, _ = (d.usuario for d in outros_docentes)
    _cadastrar(novo_tcc(), [d1, d2], as_14h, **_sala(1))

    assert _cadastrar(novo_tcc(), [d1, d3], as_14h + timedelta(hours=2), **_sala(1))

    with pytest.raises(ValidationError):
        _cadastrar(
            novo_tcc(), [d1, d3], as_14h + timedelta(hours=1, minutes=59), **_sala(2)
        )


def test_ct_ban_04_consulta_so_a_janela_de_horario(
    novo_tcc, outros_docentes, as_14h, django_assert_max_num_queries
):
    """CT-BAN-04 (parte automatizavel): a validacao nao cresce com bancas fora da janela."""
    d1, d2, *_ = (d.usuario for d in outros_docentes)
    for dias in range(1, 6):  # bancas em outros dias nao entram na consulta
        _cadastrar(novo_tcc(), [d1, d2], as_14h + timedelta(days=dias), **_sala(1))

    with django_assert_max_num_queries(2):
        validar_conflito_banca(
            data_hora_inicio=as_14h,
            tipo_local=TipoLocal.PRESENCIAL,
            bloco="NUCOMP",
            sala="1",
            usuarios_membros_ids=[d1.id],
        )


# ------------------------------------------------------------------------
# Ajustes do C4 depois da E2: mensagem que identifica a banca e trava contra
# cadastros simultaneos.
# ------------------------------------------------------------------------
def test_mensagem_de_conflito_de_membro_cita_a_banca_existente(
    novo_tcc, outros_docentes, as_14h
):
    """CT-BAN-01: o alerta cita a banca X (TCC, dia e hora) e o docente."""
    d1, d2, d3, _ = (d.usuario for d in outros_docentes)
    existente = _cadastrar(novo_tcc(), [d1, d2], as_14h, **_sala(1))

    with pytest.raises(ValidationError) as erro:
        _cadastrar(novo_tcc(), [d1, d3], as_14h + timedelta(hours=1), **_sala(2))

    mensagem = str(erro.value.detail["membros"])
    assert existente.tcc.titulo in mensagem
    assert timezone.localtime(as_14h).strftime("%d/%m às %Hh%M") in mensagem
    # o orientador e comum as duas bancas e e o primeiro membro encontrado,
    # ou outro membro em comum; em qualquer caso, um nome de membro aparece
    nomes = {u.nome_completo for u in (existente.tcc.orientador.usuario, d1)}
    assert any(nome in mensagem for nome in nomes)


def test_mensagem_de_conflito_de_local_cita_a_banca_existente(
    criar_docente, criar_aluno, area, as_14h
):
    from core.services import tcc as servico_tcc

    def tcc_e_membros():
        orientador = criar_docente()
        tcc = servico_tcc.cadastrar_tcc(
            dados={
                "titulo": f"TCC do orientador {orientador.pk}",
                "area_conhecimento": area,
                "modalidade": "DEFESA_EM_BANCA",
                "autor": criar_aluno(),
                "orientador": orientador,
            },
            usuario=orientador.usuario,
        )
        return tcc, [criar_docente().usuario, criar_docente().usuario]

    tcc_x, membros_x = tcc_e_membros()
    _cadastrar(tcc_x, membros_x, as_14h, **_sala(10))
    tcc_y, membros_y = tcc_e_membros()
    with pytest.raises(ValidationError) as erro:
        _cadastrar(tcc_y, membros_y, as_14h, **_sala(10))

    mensagem = str(erro.value.detail["local"])
    assert "sala 10 do bloco NUCOMP" in mensagem
    assert tcc_x.titulo in mensagem


def test_cadastro_de_banca_trava_a_agenda(novo_tcc, outros_docentes, as_14h):
    """O cadastro pede a trava da agenda antes de validar o conflito."""
    from unittest import mock

    from core.services import banca as servico_banca

    d1, d2, *_ = (d.usuario for d in outros_docentes)
    with mock.patch.object(
        servico_banca,
        "_travar_agenda_de_bancas",
        wraps=servico_banca._travar_agenda_de_bancas,
    ) as trava:
        _cadastrar(novo_tcc(), [d1, d2], as_14h, **_sala(1))
    trava.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_cadastros_simultaneos_conflitantes_so_um_passa(
    criar_aluno, criar_docente, area
):
    """Duas bancas conflitantes cadastradas ao mesmo tempo, em conexoes
    separadas: com a trava da agenda, exatamente uma e gravada."""
    import threading

    from django.db import connection as conexao_principal
    from django.db import connections

    from core.services import tcc as servico_tcc

    if conexao_principal.vendor != "postgresql":
        pytest.skip("a trava usa pg_advisory_xact_lock")

    orientador = criar_docente()
    membros = [criar_docente().usuario, criar_docente().usuario]
    tccs = [
        servico_tcc.cadastrar_tcc(
            dados={
                "titulo": f"TCC simultaneo {n}",
                "area_conhecimento": area,
                "modalidade": "DEFESA_EM_BANCA",
                "autor": criar_aluno(),
                "orientador": orientador,
            },
            usuario=orientador.usuario,
        )
        for n in range(2)
    ]
    inicio = timezone.now() + timedelta(days=12)
    largada = threading.Barrier(2)
    resultados = []

    def cadastrar(tcc, sala):
        try:
            largada.wait()
            _cadastrar(tcc, membros, inicio, **_sala(sala))
            resultados.append("gravou")
        except ValidationError:
            resultados.append("conflito")
        finally:
            connections.close_all()

    threads = [
        threading.Thread(target=cadastrar, args=(tcc, n)) for n, tcc in enumerate(tccs)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert sorted(resultados) == ["conflito", "gravou"]
    assert Banca.objects.filter(tcc__in=tccs).count() == 1
