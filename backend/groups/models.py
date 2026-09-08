import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils import timezone

from members.models import Member


class SavingsGroup(models.Model):
    class MeetingFrequency(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Biweekly"
        MONTHLY = "monthly", "Monthly"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=32, unique=True)
    location = models.CharField(max_length=255, blank=True)
    meeting_frequency = models.CharField(
        max_length=20, choices=MeetingFrequency.choices, default=MeetingFrequency.WEEKLY
    )
    cycle_start = models.DateField(null=True, blank=True)
    cycle_end = models.DateField(null=True, blank=True)
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="facilitated_groups"
    )
    status = models.CharField(max_length=20, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class GroupMembership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        TREASURER = "treasurer", "Treasurer"
        SECRETARY = "secretary", "Secretary"
        FACILITATOR = "facilitator", "Facilitator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(SavingsGroup, on_delete=models.CASCADE, related_name="memberships")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="group_memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    join_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "member")
        ordering = ["group", "member__membership_number"]

    def __str__(self):
        return f"{self.member} in {self.group} as {self.role}"


class Meeting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(SavingsGroup, on_delete=models.CASCADE, related_name="meetings")
    date = models.DateTimeField()
    attendance = models.ManyToManyField(GroupMembership, blank=True, related_name="attended_meetings")
    cash_start = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    cash_end = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Meeting {self.group} @ {self.date.date()}"


class Contribution(models.Model):
    class Type(models.TextChoices):
        SAVINGS = "savings", "Savings"
        FINE = "fine", "Fine"
        SHARE = "share", "Share"
        INTEREST = "interest", "Interest"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(SavingsGroup, on_delete=models.CASCADE, related_name="contributions")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="contributions")
    meeting = models.ForeignKey(Meeting, null=True, blank=True, on_delete=models.SET_NULL, related_name="contributions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SAVINGS)
    payment_method = models.CharField(max_length=50, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} - {self.amount} by {self.member}"

    def save(self, *args, **kwargs):
        is_create = self._state.adding
        super().save(*args, **kwargs)
        # Only create ledger entry on first save
        if is_create:
            # Treat contributions as credits to group balance
            LedgerEntry.create_from_source(group=self.group, amount=self.amount, source=self, entry_type=LedgerEntry.EntryType.CREDIT, created_by=self.created_by)


class LedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(SavingsGroup, on_delete=models.CASCADE, related_name="ledger_entries")
    entry_type = models.CharField(max_length=10, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)

    # Generic link to source object (Contribution, Loan, Shareout, etc)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=255, blank=True)
    source = GenericForeignKey("content_type", "object_id")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    @classmethod
    def create_from_source(cls, group, amount, source, entry_type, created_by=None):
        # compute previous balance
        with transaction.atomic():
            last = (
                cls.objects.select_for_update()
                .filter(group=group)
                .order_by("-created_at")
                .first()
            )
            prev_balance = last.balance_after if last is not None else Decimal("0.00")
            if entry_type == cls.EntryType.CREDIT:
                new_balance = prev_balance + Decimal(amount)
            else:
                new_balance = prev_balance - Decimal(amount)

            entry = cls.objects.create(
                group=group,
                entry_type=entry_type,
                amount=amount,
                balance_after=new_balance,
                content_type=ContentType.objects.get_for_model(source.__class__),
                object_id=str(source.pk),
                created_by=created_by,
            )
            return entry
