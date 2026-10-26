"""B10: o comando de dados de demonstracao cria tudo e pode rodar de novo."""

import pytest
from django.core.management import call_command

from core.models import TCC, Aluno, Banca, Docente, Usuario

pytestmark = pytest.mark.django_db


def test_popular_demo_cria_dados_e_e_idempotente(api):
    call_command("popular_demo")
    call_command("popular_demo")

    assert Docente.objects.count() == 4
    assert Aluno.objects.count() == 4
    assert TCC.objects.count() == 3
    assert Banca.objects.count() == 1
    assert Usuario.objects.filter(tipo_usuario="MEMBRO_EXTERNO").count() == 1

    resp = api.post(
        "/api/auth/login/", {"login": "DOC-002", "senha": "Demo#2026"}, format="json"
    )
    assert resp.status_code == 200
