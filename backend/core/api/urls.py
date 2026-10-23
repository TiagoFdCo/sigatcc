from rest_framework.routers import DefaultRouter

from core.api.views import BancaViewSet, TCCViewSet

router = DefaultRouter()
router.register("tccs", TCCViewSet, basename="tcc")
router.register("bancas", BancaViewSet, basename="banca")

urlpatterns = router.urls
