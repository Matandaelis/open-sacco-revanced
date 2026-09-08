@@
 from rest_framework import mixins, status, viewsets
@@
 from .services import build_eligibility_summary, disburse_application, post_installment_repayment
+from accounting.services import post_journal
@@
 	@action(detail=True, methods=["post"], url_path="disburse")
 	def disburse(self, request, application_number=None):
@@
 		try:
-			disburse_application(
-				application=application,
-				account=serializer.context["account"],
-				user=request.user,
-				notes=serializer.validated_data["disbursement_notes"],
-			)
+			# Preview mode: return the postings that would be created without executing
+			if request.query_params.get("preview") == "true":
+				# construct postings for preview using the same mapping as disburse_application
+				postings = [
+					{
+						"account_code": f"member:{application.member.id}:loan_receivable:{application.application_number}",
+						"account_name": f"Loan Receivable {application.application_number}",
+						"account_kind": "asset",
+						"entry_type": "debit",
+						"amount": str(application.requested_amount),
+					},
+					{
+						"account_code": f"group:{application.member.id}:cash",
+						"account_name": f"{application.member.membership_number} Cash",
+						"account_kind": "asset",
+						"entry_type": "credit",
+						"amount": str(application.requested_amount),
+					},
+				]
+				return Response({"preview": postings})
+			# Execution mode
+			disburse_application(
+				application=application,
+				account=serializer.context["account"],
+				user=request.user,
+				notes=serializer.validated_data["disbursement_notes"],
+			)
@@
 	@action(detail=True, methods=["post"], url_path="repay")
 	def repay(self, request, application_number=None):
@@
 		try:
-			post_installment_repayment(
-				loan=serializer.context["loan"],
-				installment_number=serializer.validated_data["installment_number"],
-				account=serializer.context["account"],
-				user=request.user,
-				narration=serializer.validated_data["narration"],
-			)
+			# preview mode: show postings that would be created
+			if request.query_params.get("preview") == "true":
+				loan = serializer.context["loan"]
+				installment = loan.schedule.get(installment_number=serializer.validated_data["installment_number"])
+				postings = [
+					{
+						"account_code": f"group:{loan.member.id}:cash",
+						"account_name": f"{loan.member.membership_number} Cash",
+						"account_kind": "asset",
+						"entry_type": "debit",
+						"amount": str(installment.total_due),
+					},
+				]
+				if installment.principal_due and installment.principal_due > 0:
+					postings.append({
+						"account_code": f"member:{loan.member.id}:loan_receivable:{loan.id}",
+						"account_name": f"Loan Receivable {loan.loan_number}",
+						"account_kind": "asset",
+						"entry_type": "credit",
+						"amount": str(installment.principal_due),
+					})
+				if installment.interest_due and installment.interest_due > 0:
+					postings.append({
+						"account_code": "income:interest",
+						"account_name": "Interest Income",
+						"account_kind": "income",
+						"entry_type": "credit",
+						"amount": str(installment.interest_due),
+					})
+				return Response({"preview": postings})
+			# execution
+			post_installment_repayment(
+				loan=serializer.context["loan"],
+				installment_number=serializer.validated_data["installment_number"],
+				account=serializer.context["account"],
+				user=request.user,
+				narration=serializer.validated_data["narration"],
+			)
*** End Patch