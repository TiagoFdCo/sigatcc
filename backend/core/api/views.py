from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api.permissions import LeituraOuGestao
from core.api.serializers import MudarSituacaoSerializer, TCCSerializer
from core.models import TCC
from core.services import tcc as servico_tcc


class TCCViewSet(viewsets.ModelViewSet):
    """/api/tccs/ (B7a) e /api/tccs/{id}/situacao/ (B7b)."""

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

    @action(detail=True, methods=["post"])
    def situacao(self, request, pk=None):
        entrada = MudarSituacaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        tcc = servico_tcc.mudar_situacao(
            tcc_id=pk, usuario=request.user, **entrada.validated_data
        )
        return Response(TCCSerializer(tcc).data)
