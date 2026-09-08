from rest_framework import serializers

from .models import SavingsGroup, GroupMembership, Meeting, Contribution, LedgerEntry


class SavingsGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsGroup
        fields = "__all__"


class GroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembership
        fields = "__all__"


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = "__all__"


class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = "__all__"


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = "__all__"
