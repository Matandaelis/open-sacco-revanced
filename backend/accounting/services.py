@@
 from decimal import Decimal
 from django.db import transaction
 from django.db.models import Sum
 
 from .models import Account, JournalEntry, Posting
 from django.contrib.contenttypes.models import ContentType
+from .models import Account as AccountingAccount
@@
 def _ensure_account(code: str, name: str, kind: str = Account.ASSET) -> Account:
     """Get or create an Account by code."""
     account, _ = Account.objects.get_or_create(code=code, defaults={"name": name, "kind": kind})
     return account
+
+
+def create_group_accounts(group):
+    """Create default accounts for a SavingsGroup."""
+    cash_code = f"group:{group.id}:cash"
+    savings_code = f"group:{group.id}:savings"
+    social_code = f"group:{group.id}:social"
+    _ensure_account(code=cash_code, name=f"{group.name} Cash", kind=Account.ASSET)
+    _ensure_account(code=savings_code, name=f"{group.name} Savings", kind=Account.LIABILITY)
+    _ensure_account(code=social_code, name=f"{group.name} Social Fund", kind=Account.LIABILITY)
+
+
+def create_member_accounts(member):
+    """Create default accounts for a Member."""
+    sav_code = f"member:{member.id}:savings"
+    _ensure_account(code=sav_code, name=f"{member.membership_number} Savings", kind=Account.LIABILITY)
+    return _ensure_account(code=sav_code, name=f"{member.membership_number} Savings", kind=Account.LIABILITY)
@@
 def post_journal(*, postings: list, narration: str = "", source=None, created_by=None) -> JournalEntry:
@@
         for p in postings:
             code = p["account_code"]
             name = p.get("account_name", code)
             kind = p.get("account_kind", Account.ASSET)
             account = _ensure_account(code=code, name=name, kind=kind)
@@
             Posting.objects.create(
                 journal=journal,
                 account=account,
                 entry_type=p["entry_type"],
                 amount=amt,
                 balance_after=new_balance,
             )
 
         return journal
