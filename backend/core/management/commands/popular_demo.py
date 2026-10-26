"""Dados de demonstracao para testes de integracao e homologacao (B10, B11).

Uso: python manage.py popular_demo [--senha "Demo#2026"]

Pode rodar mais de uma vez: o que ja existe (pelo e-mail ou titulo) e mantido.
Nao use em producao.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import TCC, AreaConhecimento, Curso, TipoUsuario, Usuario
from core.services import banca as servico_banca
from core.services import docente as servico_docente
from core.services import pessoas as servico_pessoas
from core.services import tcc as servico_tcc

AREAS = [
    "Engenharia de Software",
    "Inteligência Artificial",
    "Internet das Coisas",
    "Informática na Educação",
]

DOCENTES = [
    ("Profa. Helena Costa", "helena.costa", "SI", True),
    ("Prof. Carlos Lima", "carlos.lima", "ECP", False),
    ("Profa. Fernanda Alves", "fernanda.alves", "ECP", False),
    ("Prof. Eduardo Melo", "eduardo.melo", "LIC", False),
]

ALUNOS = [
    ("Ana Souza", "2021001234", "ENG_COMPUTACAO"),
    ("Bruno Farias", "2021002345", "SISTEMAS_INFORMACAO"),
    ("Carla Mendes", "2021003456", "LICENCIATURA_COMPUTACAO"),
    ("Davi Rocha", "2021004567", "ENG_COMPUTACAO"),
]


def gerar_cpf(n):
    """CPF valido (ficticio) a partir de um numero: 9 digitos + verificadores."""
    base = f"{n:09d}"[-9:]
    for tamanho in (9, 10):
        soma = sum(int(base[i]) * (tamanho + 1 - i) for i in range(tamanho))
        base += str((soma * 10) % 11 % 10)
    return base


class Command(BaseCommand):
    help = "Cria dados de demonstração (docentes, alunos, TCCs e uma banca)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--senha", default="Demo#2026", help="Senha das contas criadas"
        )

    @transaction.atomic
    def handle(self, *args, senha, **options):
        admin = Usuario.objects.filter(email="admin@sigatcc.local").first()
        if admin is None:
            admin = Usuario.objects.create_user(
                "admin@sigatcc.local",
                senha,
                nome_completo="Administrador SIGATCC",
                tipo_usuario=TipoUsuario.ADMINISTRADOR,
            )

        areas = {}
        for nome in AREAS:
            areas[nome], _ = AreaConhecimento.objects.get_or_create(nome=nome)

        docentes = []
        for i, (nome, login, depto, professor_tcc) in enumerate(DOCENTES, start=1):
            email = f"{login}@uea.edu.br"
            existente = Usuario.objects.filter(email=email).first()
            if existente:
                docentes.append(existente.docente)
                continue
            docentes.append(
                servico_docente.cadastrar_docente(
                    dados={
                        "nome_completo": nome,
                        "email": email,
                        "matricula_institucional": f"DOC-{i:03d}",
                        "cpf": gerar_cpf(111000000 + i * 7919),
                        "departamento": depto,
                        "professor_tcc": professor_tcc,
                        "senha_inicial": senha,
                    },
                    usuario=admin,
                )
            )

        alunos = []
        for i, (nome, matricula, curso) in enumerate(ALUNOS, start=1):
            email = f"aluno{i}@uea.edu.br"
            existente = Usuario.objects.filter(email=email).first()
            if existente:
                alunos.append(existente.aluno)
                continue
            alunos.append(
                servico_pessoas.cadastrar_aluno(
                    dados={
                        "nome_completo": nome,
                        "email": email,
                        "matricula": matricula,
                        "cpf": gerar_cpf(222000000 + i * 6271),
                        "curso": Curso.objects.get(nome=curso),
                    },
                    usuario=admin,
                )
            )

        for email, nome, tipo, extra in [
            ("secretaria@uea.edu.br", "Secretaria NUCOMP", TipoUsuario.SECRETARIA, {}),
            (
                "juliana.pires@ufam.edu.br",
                "Dra. Juliana Pires",
                TipoUsuario.MEMBRO_EXTERNO,
                {"instituicao_origem": "UFAM"},
            ),
        ]:
            if not Usuario.objects.filter(email=email).exists():
                servico_pessoas.cadastrar_usuario(
                    dados={
                        "nome_completo": nome,
                        "email": email,
                        "tipo_usuario": tipo,
                        "senha_inicial": senha,
                        **extra,
                    },
                    usuario=admin,
                )

        trabalhos = [
            (
                "Monitoramento de qualidade da água em igarapés",
                0,
                1,
                "Internet das Coisas",
                "DEFESA_EM_BANCA",
            ),
            (
                "Recomendação de orientadores por área de interesse",
                1,
                0,
                "Inteligência Artificial",
                "DEFESA_EM_BANCA",
            ),
            (
                "Jogos digitais no ensino de lógica",
                2,
                3,
                "Informática na Educação",
                "PUBLICACAO_APROVADA",
            ),
        ]
        tccs = []
        for titulo, aluno_i, orientador_i, area, modalidade in trabalhos:
            existente = TCC.objects.filter(titulo=titulo).first()
            if existente:
                tccs.append(existente)
                continue
            tccs.append(
                servico_tcc.cadastrar_tcc(
                    dados={
                        "titulo": titulo,
                        "area_conhecimento": areas[area],
                        "modalidade": modalidade,
                        "autor": alunos[aluno_i],
                        "orientador": docentes[orientador_i],
                    },
                    usuario=docentes[orientador_i].usuario,
                )
            )

        primeiro = tccs[0]
        if not hasattr(primeiro, "banca"):
            servico_banca.cadastrar_banca(
                tcc=primeiro,
                titulares=[
                    docentes[1].usuario,
                    docentes[0].usuario,
                    docentes[2].usuario,
                ],
                suplentes=[docentes[3].usuario],
                data_hora=timezone.now() + timedelta(days=14),
                tipo_local="PRESENCIAL",
                local="Sala 10, bloco NUCOMP",
                usuario=docentes[1].usuario,
            )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(f"Senha de todas as contas novas: {senha}")
        self.stdout.write("Administrador: admin@sigatcc.local")
        self.stdout.write("Professora de TCC: helena.costa@uea.edu.br (ou DOC-001)")
        self.stdout.write("Orientador com banca: carlos.lima@uea.edu.br (ou DOC-002)")
        self.stdout.write("Secretaria: secretaria@uea.edu.br")
