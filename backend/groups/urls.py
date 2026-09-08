from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SavingsGroupViewSet,
    GroupMembershipViewSet,
    MeetingViewSet,
    ContributionViewSet,
    LedgerEntryViewSet,
)

router = DefaultRouter()
router.register(r"groups", SavingsGroupViewSet, basename="groups")
router.register(r"memberships", GroupMembershipViewSet, basename="memberships")
router.register(r"meetings", MeetingViewSet, basename="meetings")
router.register(r"contributions", ContributionViewSet, basename="contributions")
router.register(r"ledger", LedgerEntryViewSet, basename="ledger")

urlpatterns = [
    path("", include(router.urls)),
]
