from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Account, JournalEntry, Posting
from .serializers import AccountSerializer, JournalSerializer


class IsFinanceOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_staff or request.user.has_perm("accounting.manage_accounting"))


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Account.objects.all().order_by("code")
    serializer_class = AccountSerializer
    permission_classes = [IsFinanceOrAdmin]


class JournalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JournalEntry.objects.all().order_by("-date")
    serializer_class = JournalSerializer
    permission_classes = [IsFinanceOrAdmin]

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        journal = self.get_object()
        serializer = self.get_serializer(journal)
        return Response(serializer.data)
