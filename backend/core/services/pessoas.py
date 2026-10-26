"""B14 (demais perfis): alunos, secretaria, administrador, membro externo e areas."""

from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from core.models import Aluno, AreaConhecimento, MembroExterno, TipoUsuario, Usuario
from core.services import contas
from core.services.auditoria import registrar

# Tipos cadastrados por /api/usuarios/. Docente (B6) e aluno tem cadastro proprio.
TIPOS_GERAIS = (
    TipoUsuario.SECRETARIA,
    TipoUsuario.ADMINISTRADOR,
    TipoUsuario.MEMBRO_EXTERNO,
)


# ================================================================= alunos
def _checar_matricula_aluno_livre(matricula, exceto=None):
    if Aluno.objects.filter(matricula=matricula).exclude(pk=exceto).exists():
        raise ValidationError({"matricula": "Já existe um aluno com esta matrícula."})


@transaction.atomic
def cadastrar_aluno(*, dados, usuario):
    """O aluno precisa existir para ser autor de TCC. Senha opcional: o login do
    aluno (RBN43) chega na E2."""
    _checar_matricula_aluno_livre(dados["matricula"])
    contas.checar_cpf_livre(dados["cpf"])
    conta = contas.criar_conta(
        email=dados["email"],
        nome_completo=dados["nome_completo"],
        tipo_usuario=TipoUsuario.ALUNO,
        senha=dados.get("senha_inicial"),
    )
    aluno = Aluno.objects.create(
        usuario=conta,
        matricula=dados["matricula"],
        cpf=dados["cpf"],
        curso=dados["curso"],
    )
    registrar(usuario, "ALUNO", conta.pk, "cadastro", None, conta.email)
    return aluno


@transaction.atomic
def atualizar_aluno(*, aluno_id, dados, usuario):
    aluno = get_object_or_404(
        Aluno.objects.select_for_update().select_related("usuario"), pk=aluno_id
    )
    conta = aluno.usuario
    if "email" in dados:
        contas.checar_email_livre(dados["email"], exceto=conta.pk)
    if "matricula" in dados:
        _checar_matricula_aluno_livre(dados["matricula"], exceto=aluno.pk)
    if "cpf" in dados:
        contas.checar_cpf_livre(dados["cpf"], exceto=aluno.pk)
    contas.atualizar_campos(
        conta,
        dados,
        ("nome_completo", "email"),
        usuario=usuario,
        entidade="ALUNO",
        registro_id=conta.pk,
    )
    contas.atualizar_campos(
        aluno,
        dados,
        ("matricula", "cpf", "curso"),
        usuario=usuario,
        entidade="ALUNO",
        registro_id=conta.pk,
    )
    return aluno


# ================================================= secretaria, admin, externo
@transaction.atomic
def cadastrar_usuario(*, dados, usuario):
    tipo = dados["tipo_usuario"]
    senha = dados.get("senha_inicial")
    externo = tipo == TipoUsuario.MEMBRO_EXTERNO
    if externo and not dados.get("instituicao_origem"):
        raise ValidationError(
            {"instituicao_origem": "Informe a instituição do membro externo."}
        )
    # O membro externo entra por token temporario (RBN54), sem senha propria.
    if not externo and not senha:
        raise ValidationError({"senha_inicial": "Informe a senha inicial."})

    conta = contas.criar_conta(
        email=dados["email"],
        nome_completo=dados["nome_completo"],
        tipo_usuario=tipo,
        senha=None if externo else senha,
    )
    if externo:
        MembroExterno.objects.create(
            usuario=conta, instituicao_origem=dados["instituicao_origem"]
        )
    registrar(usuario, tipo, conta.pk, "cadastro", None, conta.email)
    return conta


@transaction.atomic
def atualizar_usuario(*, usuario_id, dados, usuario):
    conta = get_object_or_404(
        Usuario.objects.select_for_update().filter(tipo_usuario__in=TIPOS_GERAIS),
        pk=usuario_id,
    )
    if "tipo_usuario" in dados and dados["tipo_usuario"] != conta.tipo_usuario:
        raise ValidationError(
            {"tipo_usuario": "O perfil da conta não pode ser trocado."}
        )
    if "email" in dados:
        contas.checar_email_livre(dados["email"], exceto=conta.pk)
    contas.atualizar_campos(
        conta,
        dados,
        ("nome_completo", "email"),
        usuario=usuario,
        entidade=conta.tipo_usuario,
        registro_id=conta.pk,
    )
    externo = getattr(conta, "membro_externo", None)
    if externo is not None and dados.get("instituicao_origem"):
        contas.atualizar_campos(
            externo,
            dados,
            ("instituicao_origem",),
            usuario=usuario,
            entidade=conta.tipo_usuario,
            registro_id=conta.pk,
        )
    return conta


# ===================================================== areas de conhecimento
def cadastrar_area(*, nome, usuario):
    nome = nome.strip()
    if AreaConhecimento.objects.filter(nome__iexact=nome).exists():
        raise ValidationError({"nome": "Esta área já está cadastrada."})
    area = AreaConhecimento.objects.create(nome=nome)
    registrar(usuario, "AREA_CONHECIMENTO", area.pk, "nome", None, nome)
    return area
