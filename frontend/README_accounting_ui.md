Integration: mounting LoanDetailIntegration

To embed the loan preview UI into your server-rendered loan detail page without modifying your frontend routing, add an HTML element and include the compiled React bundle that contains frontend/src/bootstrap_loan_detail.js.

Example Django template snippet (loan_detail.html):

<div id="loan-detail-root"
     data-application-number="{{ loan.application_number }}"
     data-token="{{ request.user.auth_token.key if request.user.is_authenticated }}"
     data-user='{{ request.user|json_script:"currentUser" }}'>
</div>

<!-- Include your compiled frontend bundle that contains the bootstrap_loan_detail module -->
<script src="/static/js/main.js"></script>

Notes:
- The data-user attribute expects a JSON string with at least `is_staff` and `roles` properties so the UI can perform role checks before showing the Confirm button.
- If you use a different auth mechanism (session cookie, JWT), pass token=null and the frontend will rely on cookies for authenticated requests.
