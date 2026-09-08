from django.contrib import admin

from .models import SavingsGroup, GroupMembership, Meeting, Contribution, LedgerEntry


@admin.register(SavingsGroup)
class SavingsGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "meeting_frequency", "facilitator", "status")
    search_fields = ("name", "code", "location")


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("member", "group", "role", "join_date", "status")
    search_fields = ("member__membership_number", "member__first_name", "group__name")


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("group", "date", "created_by")
    search_fields = ("group__name",)


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("group", "member", "amount", "type", "created_at")
    search_fields = ("member__membership_number", "group__name")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("group", "entry_type", "amount", "balance_after", "created_at")
    search_fields = ("group__name",)
