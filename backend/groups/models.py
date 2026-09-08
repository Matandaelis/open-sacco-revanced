@@
 class SavingsGroup(models.Model):
@@
     def __str__(self):
         return f"{self.name} ({self.code})"
+
+    def save(self, *args, **kwargs):
+        is_create = self._state.adding
+        super().save(*args, **kwargs)
+        if is_create:
+            # create accounting accounts for this group
+            try:
+                from accounting.services import create_group_accounts
+
+                create_group_accounts(self)
+            except Exception:
+                # non-fatal: don't block group creation if accounting fails
+                pass
@@
 class Contribution(models.Model):
@@
     def save(self, *args, **kwargs):
         is_create = self._state.adding
-        super().save(*args, **kwargs)
-        # Only create ledger entry on first save
-        if is_create:
-            # Treat contributions as credits to group balance
-            LedgerEntry.create_from_source(group=self.group, amount=self.amount, source=self, entry_type=LedgerEntry.EntryType.CREDIT, created_by=self.created_by)
+        super().save(*args, **kwargs)
+        # Only create accounting journal on first save
+        if is_create:
+            try:
+                from accounting.services import post_journal
+
+                postings = [
+                    {
+                        "account_code": f"group:{self.group.id}:cash",
+                        "account_name": f"{self.group.name} Cash",
+                        "account_kind": "asset",
+                        "entry_type": "debit",
+                        "amount": self.amount,
+                    },
+                    {
+                        "account_code": f"member:{self.member.id}:savings",
+                        "account_name": f"{self.member.membership_number} Savings",
+                        "account_kind": "liability",
+                        "entry_type": "credit",
+                        "amount": self.amount,
+                    },
+                ]
+                post_journal(postings=postings, narration=f"Contribution {self.pk}", source=self, created_by=self.created_by)
+            except Exception:
+                # fallback to legacy ledger entry for compatibility
+                try:
+                    from groups.models import LedgerEntry
+
+                    LedgerEntry.create_from_source(group=self.group, amount=self.amount, source=self, entry_type=LedgerEntry.EntryType.CREDIT, created_by=self.created_by)
+                except Exception:
+                    pass
