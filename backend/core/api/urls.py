from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from core.api.auth import LoginView, LogoutView, MeView
from core.api.views import (
    AlunoViewSet,
    AreaConhecimentoViewSet,
    BancaViewSet,
    CursoViewSet,
    DocenteViewSet,
    TCCViewSet,
    UsuarioViewSet,
)

router = DefaultRouter()
router.register("tccs", TCCViewSet, basename="tcc")
router.register("bancas", BancaViewSet, basename="banca")
router.register("docentes", DocenteViewSet, basename="docente")
router.register("alunos", AlunoViewSet, basename="aluno")
router.register("usuarios", UsuarioViewSet, basename="usuario")
router.register("cursos", CursoViewSet, basename="curso")
router.register("areas", AreaConhecimentoViewSet, basename="area")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    *router.urls,
]
