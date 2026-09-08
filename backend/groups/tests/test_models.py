from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone

from members.models import Member
from groups.models import SavingsGroup, GroupMembership, Meeting, Contribution, LedgerEntry

User = get_user_model()


class GroupsModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.member = Member.objects.create(
            first_name="John",
            middle_name="X",
            last_name="Doe",
            national_id="ID12345",
            phone_number="+1000000000",
            date_of_birth="1990-01-01",
            kra_pin="KRA123",
            country="Kenya",
            county="Nairobi",
            city="Nairobi",
        )
        self.group = SavingsGroup.objects.create(name="Test Group", code="testgrp", facilitator=self.user)
        self.membership = GroupMembership.objects.create(group=self.group, member=self.member, role=GroupMembership.Role.MEMBER)

    def test_meeting_and_contributions_create_ledger(self):
        meeting = Meeting.objects.create(group=self.group, date=timezone.now(), cash_start=Decimal("0.00"), created_by=self.user)
        meeting.attendance.add(self.membership)
        contribution = Contribution.objects.create(group=self.group, member=self.member, meeting=meeting, amount=Decimal("100.00"), type=Contribution.Type.SAVINGS, created_by=self.user)

        # There should be a ledger entry for the contribution
        entries = LedgerEntry.objects.filter(group=self.group).order_by("created_at")
        self.assertEqual(entries.count(), 1)
        entry = entries.first()
        self.assertEqual(entry.entry_type, LedgerEntry.EntryType.CREDIT)
        self.assertEqual(entry.amount, Decimal("100.00"))
        self.assertEqual(entry.balance_after, Decimal("100.00"))

        # create another contribution
        Contribution.objects.create(group=self.group, member=self.member, meeting=meeting, amount=Decimal("50.00"), type=Contribution.Type.SAVINGS, created_by=self.user)
        entry2 = LedgerEntry.objects.filter(group=self.group).order_by("created_at").last()
        self.assertEqual(entry2.balance_after, Decimal("150.00"))
