@@
 from django.db import models, transaction
 from django.utils.translation import gettext_lazy as _
 import uuid
 from django.utils import timezone
 from django.conf import settings
+from accounting.services import create_member_accounts
@@
     def save(self, *args, **kwargs):
         if not self.membership_number:
             with transaction.atomic():
                 self.membership_number = generate_membership_number()
-        super().save(*args, **kwargs)
+        is_create = self._state.adding
+        super().save(*args, **kwargs)
+        # create accounting member accounts on first create
+        if is_create:
+            try:
+                create_member_accounts(self)
+            except Exception:
+                # don't block member creation if accounting setup fails; log later
+                pass
@@
 class KYCDocument(models.Model):
@@
     def __str__(self):
         return f"{self.member} - {self.document_type}"
