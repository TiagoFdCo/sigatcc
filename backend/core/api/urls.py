from rest_framework.routers import DefaultRouter

from core.api.views import TCCViewSet

router = DefaultRouter()
router.register("tccs", TCCViewSet, basename="tcc")

urlpatterns = router.urls
