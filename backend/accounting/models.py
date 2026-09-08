import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class Account(models.Model):
    """Simple chart-of-accounts account model.

    code: unique code used to look up accounts (e.g. "group:123:cash", "member:45:savings").
    name: human friendly name.
    kind: one of asset/liability/equity/income/expense (affects debit/credit semantics in reports).
    """

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"

    KIND_CHOICES = [
        (ASSET, "Asset"),
        (LIABILITY, "Liability"),
        (EQUITY, "Equity"),
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=ASSET)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.name})"


class JournalEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField(default=timezone.now)
    narration = models.TextField(blank=True)

    # Generic link to source object (Contribution, LoanTransaction, etc)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=255, blank=True)
    source = GenericForeignKey("content_type", "object_id")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "created_at"]

    def __str__(self):
        return f"Journal {self.id} @ {self.date.date()}"


class Posting(models.Model):
    DEBIT = "debit"
    CREDIT = "credit"

    ENTRY_CHOICES = [
        (DEBIT, "Debit"),
        (CREDIT, "Credit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="postings")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="postings")
    entry_type = models.CharField(max_length=10, choices=ENTRY_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    # Cached running balance after this posting for quick reads (optional)
    balance_after = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.entry_type.upper()} {self.amount} -> {self.account.code}"


class MigrationRecord(models.Model):
    """Records which legacy ledger rows have been migrated to JournalEntry.

    This prevents accidental double-migration and provides an audit link to the
    original LedgerEntry and the created JournalEntry.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_model = models.CharField(max_length=255)
    legacy_pk = models.CharField(max_length=255, db_index=True)
    journal = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    migrated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("legacy_model", "legacy_pk")
        ordering = ["-migrated_at"]

    def __str__(self):
        return f"Migrated {self.legacy_model}:{self.legacy_pk} -> {self.journal_id}"
