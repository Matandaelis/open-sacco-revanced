from django.contrib import admin

from .models import Account, JournalEntry, Posting


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind")
    search_fields = ("code", "name")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "narration", "created_by")
    search_fields = ("narration",)


@admin.register(Posting)
class PostingAdmin(admin.ModelAdmin):
    list_display = ("journal", "account", "entry_type", "amount", "balance_after")
    search_fields = ("journal__narration", "account__code")
