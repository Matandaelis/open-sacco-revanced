from django.core.management.base import BaseCommand
from decimal import Decimal

from accounting.models import JournalEntry, Posting
from accounting.services import post_journal


class Command(BaseCommand):
    help = "Create reversing journals for given JournalEntry IDs.\n\nUsage: manage.py reverse_journal --journal-ids <id1,id2> --reason 'typo'"

    def add_arguments(self, parser):
        parser.add_argument("--journal-ids", type=str, required=True, help="Comma-separated journal UUIDs to reverse")
        parser.add_argument("--reason", type=str, required=False, default="Reversal requested", help="Reason for reversal")

    def handle(self, *args, **options):
        ids = [x.strip() for x in options.get("journal_ids").split(",") if x.strip()]
        reason = options.get("reason") or "Reversal requested"
        created = 0
        for jid in ids:
            try:
                orig = JournalEntry.objects.get(pk=jid)
            except JournalEntry.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Journal {jid} not found"))
                continue
            postings = []
            for p in orig.postings.all():
                rev_type = "credit" if p.entry_type == "debit" else "debit"
                postings.append({
                    "account_code": p.account.code,
                    "account_name": p.account.name,
                    "account_kind": p.account.kind,
                    "entry_type": rev_type,
                    "amount": str(p.amount),
                })
            try:
                rev = post_journal(postings=postings, narration=f"Reversal of {orig.id}: {reason}", source=orig, created_by=None)
                self.stdout.write(self.style.SUCCESS(f"Created reversal journal {rev.id} for {orig.id}"))
                created += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"Failed to create reversal for {orig.id}: {exc}"))
        self.stdout.write(self.style.SUCCESS(f"Created {created} reversal(s)"))
