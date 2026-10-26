from django.http import JsonResponse
from django.urls import include, path


def saude(request):
    """Verificacao simples de que a API esta no ar."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("saude/", saude),
    path("api/", include("core.api.urls")),
]
