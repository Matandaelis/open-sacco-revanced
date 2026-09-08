@@
-def post_installment_repayment(*, loan: LoanAccount, installment_number: int, account, user, narration=""):
+def post_installment_repayment(*, loan: LoanAccount, installment_number: int, account, user, narration=""):
@@
-        # post ledger credit for repayment
-        membership = (
-            GroupMembership.objects.filter(member=loan.member, status="active")
-            .order_by("-join_date")
-            .first()
-        )
-        if membership:
-            group = membership.group
-            LedgerEntry.create_from_source(group=group, amount=installment.total_due, source=payment, entry_type=LedgerEntry.EntryType.CREDIT, created_by=user)
+        # post double-entry journal for repayment
+        membership = (
+            GroupMembership.objects.filter(member=loan.member, status="active")
+            .order_by("-join_date")
+            .first()
+        )
+        if membership:
+            group = membership.group
+            postings = []
+            # debit group cash
+            postings.append({
+                "account_code": f"group:{group.id}:cash",
+                "account_name": f"{group.name} Cash",
+                "account_kind": "asset",
+                "entry_type": "debit",
+                "amount": installment.total_due,
+            })
+            # credit loan receivable
+            if installment.principal_due and installment.principal_due > 0:
+                postings.append({
+                    "account_code": f"member:{loan.member.id}:loan_receivable:{loan.id}",
+                    "account_name": f"Loan Receivable {loan.loan_number}",
+                    "account_kind": "asset",
+                    "entry_type": "credit",
+                    "amount": installment.principal_due,
+                })
+            # credit interest income
+            if installment.interest_due and installment.interest_due > 0:
+                postings.append({
+                    "account_code": "income:interest",
+                    "account_name": "Interest Income",
+                    "account_kind": "income",
+                    "entry_type": "credit",
+                    "amount": installment.interest_due,
+                })
+            try:
+                post_journal(postings=postings, narration=f"Installment repayment {payment.reference}", source=payment, created_by=user)
+            except Exception:
+                # fallback to legacy ledger
+                from groups.models import LedgerEntry
+
+                LedgerEntry.create_from_source(group=group, amount=installment.total_due, source=payment, entry_type=LedgerEntry.EntryType.CREDIT, created_by=user)
