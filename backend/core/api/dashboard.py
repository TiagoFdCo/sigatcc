from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.services.dashboard import obter_metricas_dashboard

class DashboardMetricasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        metricas = obter_metricas_dashboard(request.user)
        return Response(metricas)
