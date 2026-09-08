from django.contrib import admin

from .models import Account, JournalEntry, Posting, MigrationRecord
from .services import post_journal


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind")
    search_fields = ("code", "name")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "narration", "created_by")
    search_fields = ("narration",)
    actions = ["create_reversal"]

    def create_reversal(self, request, queryset):
        """Admin action: create reversing journals for selected journal entries.

        This will post a new JournalEntry with opposite postings and link to the
        original via the GenericForeignKey source field. The admin user will be
        recorded as created_by on the reversal.
        """
        created = 0
        for journal in queryset:
            # build reversed postings
            postings = []
            for p in journal.postings.all():
                rev_type = "credit" if p.entry_type == "debit" else "debit"
                postings.append({
                    "account_code": p.account.code,
                    "account_name": p.account.name,
                    "account_kind": p.account.kind,
                    "entry_type": rev_type,
                    "amount": str(p.amount),
                })
            try:
                rev = post_journal(postings=postings, narration=f"Reversal of {journal.id}", source=journal, created_by=request.user)
                created += 1
            except Exception as exc:
                self.message_user(request, f"Failed to reverse {journal.id}: {exc}", level="error")
        self.message_user(request, f"Created {created} reversal journal(s)")
    create_reversal.short_description = "Create reversal journals for selected entries"


@admin.register(Posting)
class PostingAdmin(admin.ModelAdmin):
    list_display = ("journal", "account", "entry_type", "amount", "balance_after")
    search_fields = ("journal__narration", "account__code")


@admin.register(MigrationRecord)
class MigrationRecordAdmin(admin.ModelAdmin):
    list_display = ("legacy_model", "legacy_pk", "journal", "migrated_at")
    search_fields = ("legacy_model", "legacy_pk")
