"""B6 (cadastro de docentes, RBN14 e RBN57): so o administrador escreve."""

from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from core.models import Docente, TipoUsuario
from core.services import contas
from core.services.auditoria import registrar

CAMPOS_CONTA = ("nome_completo", "email")
CAMPOS_DOCENTE = (
    "matricula_institucional",
    "cpf",
    "departamento",
    "professor_tcc",
    "aceita_orientacoes",
)


def _checar_matricula_livre(matricula, exceto=None):
    existe = (
        Docente.objects.filter(matricula_institucional=matricula)
        .exclude(pk=exceto)
        .exists()
    )
    if existe:
        raise ValidationError(
            {"matricula_institucional": "Já existe um docente com esta matrícula."}
        )


@transaction.atomic
def cadastrar_docente(*, dados, usuario):
    """Cria USUARIO (tipo DOCENTE) e DOCENTE juntos, com a senha inicial."""
    senha = dados.get("senha_inicial")
    if not senha:
        raise ValidationError({"senha_inicial": "Informe a senha inicial."})
    _checar_matricula_livre(dados["matricula_institucional"])
    contas.checar_cpf_livre(dados["cpf"])

    conta = contas.criar_conta(
        email=dados["email"],
        nome_completo=dados["nome_completo"],
        tipo_usuario=TipoUsuario.DOCENTE,
        senha=senha,
    )
    docente = Docente.objects.create(
        usuario=conta,
        matricula_institucional=dados["matricula_institucional"],
        cpf=dados["cpf"],
        departamento=dados["departamento"],
        professor_tcc=dados.get("professor_tcc", False),
        aceita_orientacoes=dados.get("aceita_orientacoes", True),
    )
    docente.areas_interesse.set(dados.get("areas_interesse", []))
    registrar(usuario, "DOCENTE", conta.pk, "cadastro", None, conta.email)
    return docente


@transaction.atomic
def atualizar_docente(*, docente_id, dados, usuario):
    docente = get_object_or_404(
        Docente.objects.select_for_update().select_related("usuario"), pk=docente_id
    )
    conta = docente.usuario
    if "email" in dados:
        contas.checar_email_livre(dados["email"], exceto=conta.pk)
    if "matricula_institucional" in dados:
        _checar_matricula_livre(dados["matricula_institucional"], exceto=docente.pk)
    if "cpf" in dados:
        contas.checar_cpf_livre(dados["cpf"], exceto=docente.pk)

    contas.atualizar_campos(
        conta,
        dados,
        CAMPOS_CONTA,
        usuario=usuario,
        entidade="DOCENTE",
        registro_id=conta.pk,
    )
    contas.atualizar_campos(
        docente,
        dados,
        CAMPOS_DOCENTE,
        usuario=usuario,
        entidade="DOCENTE",
        registro_id=conta.pk,
    )
    if "areas_interesse" in dados:
        antes = {str(a.pk) for a in docente.areas_interesse.all()}
        depois = {str(a.pk) for a in dados["areas_interesse"]}
        if antes != depois:
            docente.areas_interesse.set(dados["areas_interesse"])
            registrar(
                usuario,
                "DOCENTE",
                conta.pk,
                "areas_interesse",
                ",".join(sorted(antes)),
                ",".join(sorted(depois)),
            )
    return docente
