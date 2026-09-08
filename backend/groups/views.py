from rest_framework import viewsets, permissions

from .models import SavingsGroup, GroupMembership, Meeting, Contribution, LedgerEntry
from .serializers import (
    SavingsGroupSerializer,
    GroupMembershipSerializer,
    MeetingSerializer,
    ContributionSerializer,
    LedgerEntrySerializer,
)


class IsAuthenticatedPermission(permissions.IsAuthenticated):
    pass


class SavingsGroupViewSet(viewsets.ModelViewSet):
    queryset = SavingsGroup.objects.all()
    serializer_class = SavingsGroupSerializer
    permission_classes = [IsAuthenticatedPermission]


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.select_related("member", "group").all()
    serializer_class = GroupMembershipSerializer
    permission_classes = [IsAuthenticatedPermission]


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.select_related("group", "created_by").all()
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticatedPermission]


class ContributionViewSet(viewsets.ModelViewSet):
    queryset = Contribution.objects.select_related("group", "member", "meeting").all()
    serializer_class = ContributionSerializer
    permission_classes = [IsAuthenticatedPermission]


class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LedgerEntry.objects.select_related("group", "created_by").all()
    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticatedPermission]
