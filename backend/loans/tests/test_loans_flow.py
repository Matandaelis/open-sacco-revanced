@@
-        # ledger debit should exist for group
-        ledger = LedgerEntry.objects.filter(group=self.group).order_by("created_at").last()
-        self.assertEqual(ledger.entry_type, LedgerEntry.EntryType.DEBIT)
-        self.assertEqual(ledger.amount, Decimal("300.00"))
+        # journal entries should exist for the disbursement
+        from accounting.models import JournalEntry, Posting
+
+        journal = JournalEntry.objects.filter(content_type__model="loantransaction").order_by("created_at").last()
+        self.assertIsNotNone(journal)
+        postings = journal.postings.all()
+        # should have at least two postings
+        self.assertTrue(postings.count() >= 2)
+        amounts = [p.amount for p in postings]
+        self.assertIn(Decimal("300.00"), amounts)
@@
-        # ledger credit for repayment
-        ledger2 = LedgerEntry.objects.filter(group=self.group).order_by("created_at").last()
-        self.assertEqual(ledger2.entry_type, LedgerEntry.EntryType.CREDIT)
+        # journal entry for repayment should be created
+        journal2 = JournalEntry.objects.filter(content_type__model="loantransaction").order_by("created_at").last()
+        self.assertIsNotNone(journal2)
+        posts2 = journal2.postings.all()
+        self.assertTrue(posts2.count() >= 2)
