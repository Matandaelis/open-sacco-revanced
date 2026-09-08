from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import json

from groups.models import LedgerEntry, Contribution
from accounting.services import post_journal


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
            mapping = self._map_ledger_entry(entry, model)
            preview.append({
                "ledger_id": str(entry.pk),
                "source_model": model,
                "mappings": mapping,
            })

            if options.get("apply"):
                # create journal using post_journal; mapping contains postings list
                try:
                    postings = mapping.get("postings")
                    if postings:
                        post_journal(postings=postings, narration=f"Migrated ledger {entry.pk}", source=entry, created_by=None)
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
          - If source model is 'loantransaction' and entry_type is debit -> Disbursement mapping
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
            # Inspect object_id not guaranteed; use entry_type to guess
            if entry.entry_type == LedgerEntry.EntryType.DEBIT:
                # likely a disbursement: debit loan receivable, credit group cash
                postings = [
                    {
                        "account_code": f"member:{entry.object_id}:loan_receivable:{entry.object_id}",
                        "account_name": f"Loan Receivable {entry.object_id}",
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
                # repayment-like
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
