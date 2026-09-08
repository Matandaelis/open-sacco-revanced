from rest_framework import serializers

from accounting.models import Account, JournalEntry, Posting


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "code", "name", "kind"]


class PostingSerializer(serializers.ModelSerializer):
    account = AccountSerializer(read_only=True)

    class Meta:
        model = Posting
        fields = ["id", "account", "entry_type", "amount", "balance_after", "created_at"]


class JournalSerializer(serializers.ModelSerializer):
    postings = PostingSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = ["id", "date", "narration", "source", "created_by", "postings"]
