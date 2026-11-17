import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_dashboard_metricas_autenticado(client_autenticado):
    url = reverse('dashboard-metricas')
    response = client_autenticado.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert 'em_desenvolvimento' in response.data
    assert 'apresentados' in response.data
    assert 'nao_apresentados' in response.data
    assert 'aprovados_publicacao' in response.data
    assert 'orientacoes_por_docente' in response.data
    assert 'bancas_por_docente' in response.data
