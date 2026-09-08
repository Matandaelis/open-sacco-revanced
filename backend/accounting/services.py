from decimal import Decimal
from django.db import transaction
from django.db.models import Sum

from .models import Account, JournalEntry, Posting
from django.contrib.contenttypes.models import ContentType


MONEY = Decimal("0.01")


def _ensure_account(code: str, name: str, kind: str = Account.ASSET) -> Account:
    """Get or create an Account by code."""
    account, _ = Account.objects.get_or_create(code=code, defaults={"name": name, "kind": kind})
    return account


def _compute_prev_balance(account: Account) -> Decimal:
    """Compute the current balance for an account as (debits - credits)."""
    agg = account.postings.aggregate(
        debit=Sum("amount", filter=Posting.objects.filter(account=account, entry_type=Posting.DEBIT)),
        credit=Sum("amount", filter=Posting.objects.filter(account=account, entry_type=Posting.CREDIT)),
    )
    debit = agg.get("debit") or Decimal("0.00")
    credit = agg.get("credit") or Decimal("0.00")
    return (debit - credit).quantize(MONEY)


def post_journal(*, postings: list, narration: str = "", source=None, created_by=None) -> JournalEntry:
    """Create a JournalEntry with multiple Postings.

    postings: list of {account_code, account_name(optional), entry_type: 'debit'|'credit', amount}
    source: optional model instance to link to the journal via GenericForeignKey
    """
    # Validate postings sum to zero (debits == credits)
    total = Decimal("0.00")
    for p in postings:
        amt = Decimal(p["amount"])
        if p["entry_type"] == Posting.DEBIT:
            total += amt
        else:
            total -= amt
    if total.quantize(MONEY) != Decimal("0.00"):
        raise ValueError("Journal postings must balance (debits == credits).")

    with transaction.atomic():
        journal = JournalEntry.objects.create(
            narration=narration,
            created_by=created_by,
        )

        if source is not None:
            ct = ContentType.objects.get_for_model(source.__class__)
            journal.content_type = ct
            journal.object_id = str(source.pk)
            journal.save(update_fields=["content_type", "object_id"])  # attach source

        for p in postings:
            code = p["account_code"]
            name = p.get("account_name", code)
            kind = p.get("account_kind", Account.ASSET)
            account = _ensure_account(code=code, name=name, kind=kind)

            # compute previous balance for the account and update balance_after
            # we compute (debits - credits)
            prev_balance_agg = account.postings.aggregate(
                debit=Sum("amount", filter=Posting.objects.filter(account=account, entry_type=Posting.DEBIT)),
                credit=Sum("amount", filter=Posting.objects.filter(account=account, entry_type=Posting.CREDIT)),
            )
            prev_debit = prev_balance_agg.get("debit") or Decimal("0.00")
            prev_credit = prev_balance_agg.get("credit") or Decimal("0.00")
            prev_balance = (prev_debit - prev_credit).quantize(MONEY)

            amt = Decimal(p["amount"]).quantize(MONEY)
            if p["entry_type"] == Posting.DEBIT:
                new_balance = (prev_balance + amt).quantize(MONEY)
            else:
                new_balance = (prev_balance - amt).quantize(MONEY)

            Posting.objects.create(
                journal=journal,
                account=account,
                entry_type=p["entry_type"],
                amount=amt,
                balance_after=new_balance,
            )

        return journal
