import pytest
from django.urls import reverse
from rest_framework import status

from core.models import Usuario


@pytest.mark.django_db
def test_dashboard_metricas_autenticado(client):
    usuario = Usuario.objects.create_user(
        email="teste_dashboard@uea.edu.br",
        cpf="00000000000",
        nome_completo="Usuario Teste Dashboard",
        tipo_usuario="ADMINISTRADOR",
    )
    client.force_login(usuario)

    url = reverse("dashboard-metricas")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "em_desenvolvimento" in response.data
    assert "apresentados" in response.data
    assert "nao_apresentados" in response.data
    assert "aprovados_publicacao" in response.data
    assert "orientacoes_por_docente" in response.data
    assert "bancas_por_docente" in response.data
