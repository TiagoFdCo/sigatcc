import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Usuario


@pytest.mark.django_db
def test_dashboard_metricas_autenticado():
    usuario = Usuario.objects.create_user(
        email="teste_dashboard@uea.edu.br",
        nome_completo="Usuario Teste Dashboard",
        tipo_usuario="ADMINISTRADOR",
    )
    client = APIClient()
    client.force_authenticate(user=usuario)

    url = reverse("dashboard-metricas")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "em_desenvolvimento" in response.data
    assert "apresentados" in response.data
    assert "nao_apresentados" in response.data
    assert "aprovados_publicacao" in response.data
    assert "orientacoes_por_docente" in response.data
    assert "bancas_por_docente" in response.data


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("tipo_usuario", "esperado"),
    [
        ("ADMINISTRADOR", status.HTTP_200_OK),
        ("DOCENTE", status.HTTP_200_OK),
        ("SECRETARIA", status.HTTP_200_OK),
        ("ALUNO", status.HTTP_403_FORBIDDEN),
        ("MEMBRO_EXTERNO", status.HTTP_403_FORBIDDEN),
    ],
)
def test_dashboard_metricas_so_para_perfis_de_gestao(tipo_usuario, esperado):
    """Aluno e membro externo nao veem os indicadores nem a carga dos docentes."""
    usuario = Usuario.objects.create_user(
        email=f"dash_{tipo_usuario.lower()}@uea.edu.br",
        nome_completo=f"Usuario {tipo_usuario}",
        tipo_usuario=tipo_usuario,
    )
    client = APIClient()
    client.force_authenticate(user=usuario)

    response = client.get(reverse("dashboard-metricas"))

    assert response.status_code == esperado


@pytest.mark.django_db
def test_dashboard_metricas_exige_login():
    response = APIClient().get(reverse("dashboard-metricas"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
