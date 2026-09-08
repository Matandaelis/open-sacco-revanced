@@
-from groups.models import LedgerEntry
+from groups.models import LedgerEntry
+from accounting.services import post_journal
@@
             # post ledger entry: loan disbursement is a debit to group funds
-            group = self._get_member_group()
-            LedgerEntry.create_from_source(group=group, amount=self.principal_amount, source=tx, entry_type=LedgerEntry.EntryType.DEBIT, created_by=user)
+            group = self._get_member_group()
+            # create double-entry journal: Debit loan receivable (member loan asset), Credit group cash
+            postings = [
+                {
+                    "account_code": f"member:{self.member.id}:loan_receivable:{self.id}",
+                    "account_name": f"Loan Receivable {self.loan_number}",
+                    "account_kind": "asset",
+                    "entry_type": "debit",
+                    "amount": self.principal_amount,
+                },
+                {
+                    "account_code": f"group:{group.id}:cash",
+                    "account_name": f"{group.name} Cash",
+                    "account_kind": "asset",
+                    "entry_type": "credit",
+                    "amount": self.principal_amount,
+                },
+            ]
+            try:
+                post_journal(postings=postings, narration=f"Loan disbursement {tx.reference}", source=tx, created_by=user)
+            except Exception:
+                # fallback to legacy ledger entry
+                LedgerEntry.create_from_source(group=group, amount=self.principal_amount, source=tx, entry_type=LedgerEntry.EntryType.DEBIT, created_by=user)
@@
-            # post ledger entry: repayment is credit to group funds
-            group = self._get_member_group()
-            LedgerEntry.create_from_source(group=group, amount=amt, source=tx, entry_type=LedgerEntry.EntryType.CREDIT, created_by=user)
+            # post journal entries for repayment: allocate to principal and interest
+            membership = (
+                GroupMembership.objects.filter(member=self.member, status="active")
+                .order_by("-join_date")
+                .first()
+            )
+            if membership:
+                group = membership.group
+                postings = []
+                # cash debit
+                postings.append({
+                    "account_code": f"group:{group.id}:cash",
+                    "account_name": f"{group.name} Cash",
+                    "account_kind": "asset",
+                    "entry_type": "debit",
+                    "amount": amt,
+                })
+                if interest_paid > 0:
+                    postings.append({
+                        "account_code": "income:interest",
+                        "account_name": "Interest Income",
+                        "account_kind": "income",
+                        "entry_type": "credit",
+                        "amount": interest_paid,
+                    })
+                if principal_paid > 0:
+                    postings.append({
+                        "account_code": f"member:{self.member.id}:loan_receivable:{self.id}",
+                        "account_name": f"Loan Receivable {self.loan_number}",
+                        "account_kind": "asset",
+                        "entry_type": "credit",
+                        "amount": principal_paid,
+                    })
+                try:
+                    post_journal(postings=postings, narration=f"Loan repayment {tx.reference}", source=tx, created_by=user)
+                except Exception:
+                    # fallback to legacy ledger entry
+                    LedgerEntry.create_from_source(group=group, amount=amt, source=tx, entry_type=LedgerEntry.EntryType.CREDIT, created_by=user)
