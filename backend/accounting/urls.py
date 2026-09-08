from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, JournalViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"journals", JournalViewSet, basename="journal")

urlpatterns = router.urls
