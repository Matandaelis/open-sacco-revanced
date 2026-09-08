Integration instructions

1) Add the template include to your loan detail template (for example templates/loans/loan_detail.html):

   {% load static %}
   {% include 'accounting/loan_preview_embed.html' %}

2) Ensure the frontend bundle that contains the bootstrap_loan_detail.js is built and copied to your static files directory at the path used above (default: static/js/main.js). If you build to a different filename/path, update the <script> src in the include file.

3) The include expects the template context to provide `loan` (with `application_number`). If your loan detail template uses a different variable name, pass it when including:

   {% include 'accounting/loan_preview_embed.html' with loan=the_loan_object %}

4) If you use session-based auth (Django cookies), you can leave data-token empty; the frontend will use cookies for authenticated requests. If you use token auth, ensure request.user.auth_token is available in the template context (you may need to create tokens for users) or provide the token some other way.

5) Optional: restrict rendering to authorized users in the template if desired:

   {% if request.user.is_staff or request.user|has_role:'loan' %}
       {% include 'accounting/loan_preview_embed.html' %}
   {% endif %}

6) Build the frontend bundle and deploy static files:

   cd frontend
   npm install
   npm run build
   # copy build output to your Django static/ directory or run collectstatic
   python manage.py collectstatic

7) Open a loan detail page in the browser; you should see Disburse/Repay buttons rendered by the React component. Use the preview then confirm flow and verify journals in the admin.
