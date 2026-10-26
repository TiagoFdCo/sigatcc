"""B5: /api/auth/login/, /refresh/, /logout/ e /me/."""

from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from core.services import acesso

HTTP_423_LOCKED = 423


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(max_length=254)
    senha = serializers.CharField(max_length=128, trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


def dados_usuario(usuario):
    """O que a SPA precisa saber de quem esta logado."""
    docente = getattr(usuario, "docente", None)
    return {
        "id": str(usuario.pk),
        "nome_completo": usuario.nome_completo,
        "email": usuario.email,
        "tipo_usuario": usuario.tipo_usuario,
        "professor_tcc": bool(docente and docente.professor_tcc),
    }


def emitir_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    refresh["tipo_usuario"] = usuario.tipo_usuario
    refresh["nome"] = usuario.nome_completo
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def ip_da_requisicao(request):
    # Atras do nginx de producao o IP real vem em X-Real-IP (nginx/prod.conf)
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        entrada = LoginSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            usuario = acesso.autenticar(
                login=entrada.validated_data["login"],
                senha=entrada.validated_data["senha"],
                ip=ip_da_requisicao(request),
            )
        except acesso.ContaBloqueada as erro:
            return Response(
                {
                    "detail": "Conta bloqueada por 15 minutos após 5 tentativas sem sucesso.",
                    "code": "conta_bloqueada",
                    "bloqueado_ate": erro.ate.isoformat(),
                },
                status=HTTP_423_LOCKED,
            )
        except acesso.CredenciaisInvalidas:
            return Response(
                {
                    "detail": "E-mail, matrícula ou senha incorretos.",
                    "code": "credenciais_invalidas",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({**emitir_tokens(usuario), "usuario": dados_usuario(usuario)})


class LogoutView(APIView):
    """Invalida o refresh token no servidor (lista negra do simplejwt).

    Nao exige o access: quem tem o refresh pode encerrar a sessao mesmo com o
    access ja vencido.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        entrada = LogoutSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            RefreshToken(entrada.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response(
                {"detail": "Token inválido ou expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(dados_usuario(request.user))
