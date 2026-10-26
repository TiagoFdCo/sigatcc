"""Regras comuns a toda conta de usuario (B6 e B14): unicidade, senha, ativacao."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from core.models import Aluno, Docente, Usuario
from core.services.auditoria import registrar


def checar_email_livre(email, exceto=None):
    if Usuario.objects.filter(email__iexact=email).exclude(pk=exceto).exists():
        raise ValidationError({"email": "Já existe uma conta com este e-mail."})


def checar_cpf_livre(cpf, exceto=None):
    """O CPF identifica a pessoa: nao pode repetir entre docentes e alunos."""
    usado = (
        Docente.objects.filter(cpf=cpf).exclude(pk=exceto).exists()
        or Aluno.objects.filter(cpf=cpf).exclude(pk=exceto).exists()
    )
    if usado:
        raise ValidationError({"cpf": "Já existe uma pessoa cadastrada com este CPF."})


def validar_senha(senha, campo="senha_inicial"):
    try:
        validate_password(senha)
    except DjangoValidationError as erro:
        raise ValidationError({campo: erro.messages}) from None


def criar_conta(*, email, nome_completo, tipo_usuario, senha=None):
    """Cria o USUARIO base. Sem senha, a conta fica sem login ate definirem uma."""
    checar_email_livre(email)
    if senha:
        validar_senha(senha)
    return Usuario.objects.create_user(
        email, senha or None, nome_completo=nome_completo, tipo_usuario=tipo_usuario
    )


def atualizar_campos(objeto, dados, campos, *, usuario, entidade, registro_id):
    """Aplica os campos que mudaram, grava um log por campo e devolve os nomes."""
    alterados = []
    for campo in campos:
        if campo not in dados:
            continue
        anterior, novo = getattr(objeto, campo), dados[campo]
        if anterior == novo:
            continue
        setattr(objeto, campo, novo)
        alterados.append(campo)
        registrar(usuario, entidade, registro_id, campo, anterior, novo)
    if alterados:
        objeto.save(update_fields=alterados)
    return alterados


@transaction.atomic
def alterar_ativo(*, usuario_id, ativo, usuario, entidade):
    """Desativa ou reativa a conta (nunca apaga: RBN57)."""
    conta = get_object_or_404(Usuario.objects.select_for_update(), pk=usuario_id)
    if conta.pk == usuario.pk and not ativo:
        raise ValidationError("Você não pode desativar a própria conta.")
    if conta.ativo != ativo:
        registrar(usuario, entidade, conta.pk, "ativo", conta.ativo, ativo)
        conta.ativo = ativo
        conta.save(update_fields=["ativo"])
    return conta
