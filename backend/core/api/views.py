from rest_framework import viewsets

from core.api.permissions import LeituraOuGestao
from core.api.serializers import TCCSerializer
from core.models import TCC
from core.services import tcc as servico_tcc


class TCCViewSet(viewsets.ModelViewSet):
    """/api/tccs/ (B7a): listar, detalhar, cadastrar e editar."""

    queryset = TCC.objects.select_related(
        "curso", "area_conhecimento", "autor", "orientador", "coorientador"
    ).order_by("-data_cadastro")
    serializer_class = TCCSerializer
    permission_classes = [LeituraOuGestao]
    # Sem DELETE: TCC nao se apaga, e inativado com motivo (RD13)
    http_method_names = ["get", "post", "patch", "head", "options"]

    def perform_create(self, serializer):
        serializer.instance = servico_tcc.cadastrar_tcc(
            dados=serializer.validated_data, usuario=self.request.user
        )

    def perform_update(self, serializer):
        serializer.instance = servico_tcc.atualizar_tcc(
            tcc_id=serializer.instance.pk,
            dados=serializer.validated_data,
            usuario=self.request.user,
        )
