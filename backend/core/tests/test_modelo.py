import itertools
from datetime import timedelta

import pytest
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone

from core.models import (
    AreaConhecimento,
    Aluno,
    Banca,
    Curso,
    Docente,
    LogAcesso,
    MembroExterno,
    ParticipacaoBanca,
    TCC,
    TokenAcesso,
    Usuario,
)

pytestmark = pytest.mark.django_db

_contador = itertools.count(1)


def novo_usuario(tipo="ALUNO"):
    n = next(_contador)
    return Usuario.objects.create_user(
        f"usuario{n}@teste.com",
        "senha-forte-123",
        nome_completo=f"Usuario {n}",
        tipo_usuario=tipo,
    )


def novo_docente():
    n = next(_contador)
    return Docente.objects.create(
        usuario=novo_usuario("DOCENTE"),
        matricula_institucional=f"M{n}",
        cpf=f"{n:011d}",
        departamento="SI",
    )


def novo_aluno():
    n = next(_contador)
    return Aluno.objects.create(
        usuario=novo_usuario("ALUNO"),
        matricula=f"A{n}",
        cpf=f"{n + 50000:011d}",
        curso=Curso.objects.first(),
    )


def novo_tcc(aluno, orientador, **extra):
    area, _ = AreaConhecimento.objects.get_or_create(nome="Inteligencia Artificial")
    dados = dict(
        titulo="Um TCC",
        curso=aluno.curso,
        area_conhecimento=area,
        modalidade="DEFESA_EM_BANCA",
        autor=aluno,
        orientador=orientador,
    )
    dados.update(extra)
    return TCC.objects.create(**dados)


def nova_banca(tcc):
    return Banca.objects.create(
        tcc=tcc,
        data_hora=timezone.now() + timedelta(days=7),
        tipo_local="REMOTO",
        local="https://meet.exemplo.com/abc",
    )


def test_cursos_semeados():
    nomes = set(Curso.objects.values_list("nome", flat=True))
    assert nomes == {"ENG_COMPUTACAO", "SISTEMAS_INFORMACAO", "LICENCIATURA_COMPUTACAO"}


def test_create_superuser_define_administrador():
    admin = Usuario.objects.create_superuser(
        "admin@teste.com", "senha-forte-123", nome_completo="Admin"
    )
    assert admin.tipo_usuario == "ADMINISTRADOR"
    assert admin.is_active


def test_tipo_usuario_fora_da_lista_e_recusado():
    with pytest.raises(IntegrityError), transaction.atomic():
        Usuario.objects.create_user(
            "x@teste.com", "senha-forte-123", nome_completo="X", tipo_usuario="QUALQUER"
        )


def test_um_tcc_ativo_por_aluno_e_curso():
    aluno, orientador = novo_aluno(), novo_docente()
    novo_tcc(aluno, orientador)
    with pytest.raises(IntegrityError), transaction.atomic():
        novo_tcc(aluno, orientador)


def test_tcc_inativo_nao_conta_para_a_unicidade():
    aluno, orientador = novo_aluno(), novo_docente()
    novo_tcc(aluno, orientador, ativo=False, motivo_inativacao="Troca de tema")
    novo_tcc(aluno, orientador)


def test_coorientador_igual_ao_orientador_e_recusado():
    aluno, orientador = novo_aluno(), novo_docente()
    with pytest.raises(IntegrityError), transaction.atomic():
        novo_tcc(aluno, orientador, coorientador=orientador)


def test_nao_apresentado_exige_motivo():
    aluno, orientador = novo_aluno(), novo_docente()
    with pytest.raises(IntegrityError), transaction.atomic():
        novo_tcc(aluno, orientador, status="NAO_APRESENTADO")
    novo_tcc(
        aluno, orientador, status="NAO_APRESENTADO", motivo_nao_apresentacao="DESISTENCIA"
    )


def test_motivo_outro_exige_descricao():
    aluno, orientador = novo_aluno(), novo_docente()
    with pytest.raises(IntegrityError), transaction.atomic():
        novo_tcc(
            aluno,
            orientador,
            status="NAO_APRESENTADO",
            motivo_nao_apresentacao="OUTRO",
        )


def test_inativar_exige_motivo():
    aluno, orientador = novo_aluno(), novo_docente()
    with pytest.raises(IntegrityError), transaction.atomic():
        novo_tcc(aluno, orientador, ativo=False)


def test_status_fora_da_lista_e_recusado():
    aluno, orientador = novo_aluno(), novo_docente()
    with pytest.raises(IntegrityError), transaction.atomic():
        novo_tcc(aluno, orientador, status="INEXISTENTE")


def test_uma_banca_por_tcc():
    tcc = novo_tcc(novo_aluno(), novo_docente())
    nova_banca(tcc)
    with pytest.raises(IntegrityError), transaction.atomic():
        nova_banca(tcc)


def test_mesma_pessoa_nao_repete_na_banca():
    banca = nova_banca(novo_tcc(novo_aluno(), novo_docente()))
    docente = novo_docente()
    ParticipacaoBanca.objects.create(banca=banca, usuario=docente.usuario, tipo_membro="TITULAR")
    with pytest.raises(IntegrityError), transaction.atomic():
        ParticipacaoBanca.objects.create(
            banca=banca, usuario=docente.usuario, tipo_membro="SUPLENTE"
        )


def test_so_suplente_pode_ter_substituido_titular():
    banca = nova_banca(novo_tcc(novo_aluno(), novo_docente()))
    with pytest.raises(IntegrityError), transaction.atomic():
        ParticipacaoBanca.objects.create(
            banca=banca,
            usuario=novo_docente().usuario,
            tipo_membro="TITULAR",
            substituiu_titular=True,
        )
    ParticipacaoBanca.objects.create(
        banca=banca,
        usuario=novo_docente().usuario,
        tipo_membro="SUPLENTE",
        substituiu_titular=True,
    )


def test_um_token_por_membro_externo_e_banca():
    banca = nova_banca(novo_tcc(novo_aluno(), novo_docente()))
    externo = MembroExterno.objects.create(
        usuario=novo_usuario("MEMBRO_EXTERNO"), instituicao_origem="UFAM"
    )
    expira = banca.data_hora + timedelta(hours=48)
    TokenAcesso.objects.create(
        membro_externo=externo, banca=banca, token_hash="a" * 64, expira_em=expira
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        TokenAcesso.objects.create(
            membro_externo=externo, banca=banca, token_hash="b" * 64, expira_em=expira
        )


def test_log_de_acesso_so_de_acrescimo():
    log = LogAcesso.objects.create(usuario=novo_usuario(), ip="127.0.0.1")
    with pytest.raises(DatabaseError), transaction.atomic():
        LogAcesso.objects.filter(pk=log.pk).update(ip="10.0.0.1")
    with pytest.raises(DatabaseError), transaction.atomic():
        log.delete()
