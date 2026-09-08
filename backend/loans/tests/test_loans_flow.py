from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone

from members.models import Member
from groups.models import SavingsGroup, GroupMembership
from accounts.models import SavingsProduct, SavingsAccount
from accounts.services import post_savings_transaction
from loans.models import LoanProduct, LoanApplication, LoanAccount, LoanSchedule, LoanTransaction
from loans import services
from groups.models import LedgerEntry

User = get_user_model()


class LoansFlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="loanofficer", password="pass")
        # create member
        self.member = Member.objects.create(
            first_name="Alice",
            middle_name="Y",
            last_name="Member",
            national_id="ID99999",
            phone_number="+1999999999",
            date_of_birth="1992-02-02",
            kra_pin="KRA999",
            country="Kenya",
            county="Nairobi",
            city="Nairobi",
        )
        # group and membership
        self.group = SavingsGroup.objects.create(name="Loan Group", code="loangrp", facilitator=self.user)
        self.membership = GroupMembership.objects.create(group=self.group, member=self.member, role=GroupMembership.Role.MEMBER)

        # savings product and account
        self.product = SavingsProduct.objects.create(name="Default", code="DEF", minimum_balance=Decimal("0.00"), interest_rate=Decimal("0.00"))
        self.account = SavingsAccount.objects.create(member=self.member, product=self.product)

        # fund account
        post_savings_transaction(account=self.account, transaction_type="deposit", amount=Decimal("1000.00"), user=self.user, narration="seed")

        # loan product
        self.loan_product = LoanProduct.objects.create(name="Standard", interest_rate=Decimal("12.00"), repayment_period_months=6, multiplier=Decimal("3.00"), interest_type=LoanProduct.REDUCING, min_amount=Decimal("10.00"), max_amount=Decimal("10000.00"), max_term_months=12, requires_guarantors=False)

    def test_application_approve_disburse_and_repay(self):
        application = LoanApplication.objects.create(member=self.member, loan_type=self.loan_product, requested_amount=Decimal("300.00"), purpose="Test", repayment_period_months=6, created_by=self.user)
        # approve
        application.start_review(self.user)
        application.approve(self.user, notes="OK")
        self.assertEqual(application.status, LoanApplication.Status.APPROVED)

        # disburse via service
        loan_account = services.disburse_application(application=application, account=self.account, user=self.user, notes="disb")
        self.assertIsInstance(loan_account, LoanAccount)
        self.assertEqual(loan_account.status, LoanAccount.DISBURSED)

        # ledger debit should exist for group
        ledger = LedgerEntry.objects.filter(group=self.group).order_by("created_at").last()
        self.assertEqual(ledger.entry_type, LedgerEntry.EntryType.DEBIT)
        self.assertEqual(ledger.amount, Decimal("300.00"))

        # schedules should exist
        schedules = LoanSchedule.objects.filter(loan=loan_account).order_by("installment_number")
        self.assertEqual(schedules.count(), 6)

        # repay first installment using service
        inst = schedules.first()
        services.post_installment_repayment(loan=loan_account, installment_number=inst.installment_number, account=self.account, user=self.user, narration="repay 1")
        inst.refresh_from_db()
        self.assertTrue(inst.is_paid)

        # ledger credit for repayment
        ledger2 = LedgerEntry.objects.filter(group=self.group).order_by("created_at").last()
        self.assertEqual(ledger2.entry_type, LedgerEntry.EntryType.CREDIT)
