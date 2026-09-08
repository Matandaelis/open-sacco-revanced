from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import json

from groups.models import LedgerEntry, Contribution
from accounting.services import post_journal
from accounting.models import MigrationRecord

# Try to import LoanTransaction for better loan mappings
try:
    from loans.models import LoanTransaction
except Exception:
    LoanTransaction = None


class Command(BaseCommand):
    help = "Migrate legacy groups.LedgerEntry rows into accounting.JournalEntry + Posting records.\n\nUse --dry-run to preview changes without applying. Use --limit N to limit processed rows."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", dest="dry_run", default=True,
                            help="Preview migration without applying (default: True)")
        parser.add_argument("--apply", action="store_true", dest="apply", default=False,
                            help="Apply the migration (destructive if run twice).")
        parser.add_argument("--limit", type=int, dest="limit", default=100,
                            help="Limit number of entries to process (for dry-run/testing).")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run") and not options.get("apply")
        limit = options.get("limit") or 100

        qs = LedgerEntry.objects.select_related("content_type").order_by("created_at")[:limit]

        preview = []
        applied = 0

        for entry in qs:
            model = entry.content_type.model if entry.content_type else None
            legacy_model = model or "ledger"
            legacy_pk = str(entry.pk)

            # Skip already-migrated rows
            if MigrationRecord.objects.filter(legacy_model=legacy_model, legacy_pk=legacy_pk).exists():
                # include a short note in preview
                preview.append({
                    "ledger_id": legacy_pk,
                    "source_model": model,
                    "skipped": True,
                    "reason": "already migrated",
                })
                continue

            mapping = self._map_ledger_entry(entry, model)
            preview.append({
                "ledger_id": legacy_pk,
                "source_model": model,
                "mappings": mapping,
            })

            if options.get("apply"):
                # create journal using post_journal; mapping contains postings list
                try:
                    postings = mapping.get("postings")
                    if postings:
                        journal = post_journal(postings=postings, narration=f"Migrated ledger {entry.pk}", source=entry, created_by=None)
                        # record migration to avoid duplicate processing
                        try:
                            MigrationRecord.objects.create(
                                legacy_model=legacy_model,
                                legacy_pk=legacy_pk,
                                journal=journal,
                            )
                        except Exception:
                            # Non-fatal: if recording fails, still continue but warn in stdout
                            self.stdout.write(self.style.WARNING(f"Failed to record migration for ledger {entry.pk}"))
                        applied += 1
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f"Failed to migrate ledger {entry.pk}: {exc}"))

        # output preview as JSON
        out = {
            "dry_run": dry_run,
            "count_previewed": len(preview),
            "applied": applied,
            "preview": preview,
        }

        self.stdout.write(json.dumps(out, default=str, indent=2))

    def _map_ledger_entry(self, entry: LedgerEntry, model: str):
        """Return a mapping dict with postings list for the ledger entry.

        Heuristic mapping rules:
          - If source model is 'contribution' -> Debit group:{group}:cash, Credit member:{member}:savings
          - If source model is 'loantransaction' and entry_type is debit -> Disbursement mapping (uses LoanTransaction if available)
          - Otherwise fall back to Debit group cash / Credit group savings (neutral)
        """
        postings = []
        amount = Decimal(entry.amount)

        if model == "contribution":
            # Try to fetch contribution to discover member
            try:
                contrib = Contribution.objects.get(pk=entry.object_id)
                postings = [
                    {
                        "account_code": f"group:{entry.group.id}:cash",
                        "account_name": f"{entry.group.name} Cash",
                        "account_kind": "asset",
                        "entry_type": "debit",
                        "amount": str(amount),
                    },
                    {
                        "account_code": f"member:{contrib.member.id}:savings",
                        "account_name": f"{contrib.member.membership_number} Savings",
                        "account_kind": "liability",
                        "entry_type": "credit",
                        "amount": str(amount),
                    },
                ]
            except Exception:
                # fallback neutral mapping
                postings = [
                    {
                        "account_code": f"group:{entry.group.id}:cash",
                        "account_name": f"{entry.group.name} Cash",
                        "account_kind": "asset",
                        "entry_type": "debit",
                        "amount": str(amount),
                    },
                    {
                        "account_code": f"group:{entry.group.id}:savings",
                        "account_name": f"{entry.group.name} Savings",
                        "account_kind": "liability",
                        "entry_type": "credit",
                        "amount": str(amount),
                    },
                ]
        elif model == "loantransaction":
            # Try to resolve the actual LoanTransaction -> LoanAccount -> Member
            try:
                if LoanTransaction is not None:
                    tx = LoanTransaction.objects.select_related("loan", "loan__member").get(pk=entry.object_id)
                    loan = tx.loan
                    member = loan.member
                    if entry.entry_type == LedgerEntry.EntryType.DEBIT:
                        # disbursement: debit loan receivable (per-loan), credit group cash
                        postings = [
                            {
                                "account_code": f"member:{member.id}:loan_receivable:{loan.id}",
                                "account_name": f"Loan Receivable {loan.loan_number}",
                                "account_kind": "asset",
                                "entry_type": "debit",
                                "amount": str(amount),
                            },
                            {
                                "account_code": f"group:{entry.group.id}:cash",
                                "account_name": f"{entry.group.name} Cash",
                                "account_kind": "asset",
                                "entry_type": "credit",
                                "amount": str(amount),
                            },
                        ]
                    else:
                        # repayment: attempt to split principal/interest if tx has fields
                        principal = None
                        interest = None
                        # try common field names if present
                        if hasattr(tx, "principal_paid") and hasattr(tx, "interest_paid"):
                            principal = Decimal(getattr(tx, "principal_paid") or 0)
                            interest = Decimal(getattr(tx, "interest_paid") or 0)
                        elif hasattr(tx, "principal") and hasattr(tx, "interest"):
                            principal = Decimal(getattr(tx, "principal") or 0)
                            interest = Decimal(getattr(tx, "interest") or 0)

                        postings = []
                        postings.append({
                            "account_code": f"group:{entry.group.id}:cash",
                            "account_name": f"{entry.group.name} Cash",
                            "account_kind": "asset",
                            "entry_type": "debit",
                            "amount": str(amount),
                        })

                        if principal and principal > 0:
                            postings.append({
                                "account_code": f"member:{member.id}:loan_receivable:{loan.id}",
                                "account_name": f"Loan Receivable {loan.loan_number}",
                                "account_kind": "asset",
                                "entry_type": "credit",
                                "amount": str(principal),
                            })
                        if interest and interest > 0:
                            postings.append({
                                "account_code": "income:interest",
                                "account_name": "Interest Income",
                                "account_kind": "income",
                                "entry_type": "credit",
                                "amount": str(interest),
                            })

                        # If we couldn't split, post as credit to loan receivable
                        if len(postings) == 1:
                            postings.append({
                                "account_code": f"member:{member.id}:loan_receivable:{loan.id}",
                                "account_name": f"Loan Receivable {loan.loan_number}",
                                "account_kind": "asset",
                                "entry_type": "credit",
                                "amount": str(amount),
                            })
                else:
                    raise Exception("LoanTransaction model not available")
            except Exception:
                # fallback to prior generic mapping
                postings = [
                    {
                        "account_code": f"group:{entry.group.id}:cash",
                        "account_name": f"{entry.group.name} Cash",
                        "account_kind": "asset",
                        "entry_type": "debit",
                        "amount": str(amount),
                    },
                    {
                        "account_code": f"group:{entry.group.id}:savings",
                        "account_name": f"{entry.group.name} Savings",
                        "account_kind": "liability",
                        "entry_type": "credit",
                        "amount": str(amount),
                    },
                ]
        else:
            # generic mapping
            postings = [
                {
                    "account_code": f"group:{entry.group.id}:cash",
                    "account_name": f"{entry.group.name} Cash",
                    "account_kind": "asset",
                    "entry_type": "debit",
                    "amount": str(amount),
                },
                {
                    "account_code": f"group:{entry.group.id}:savings",
                    "account_name": f"{entry.group.name} Savings",
                    "account_kind": "liability",
                    "entry_type": "credit",
                    "amount": str(amount),
                },
            ]

        return {"postings": postings}
