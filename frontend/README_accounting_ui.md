# Accounting UI README

This folder contains simple React components to preview and execute loan disbursements and repayments using the backend preview endpoints added in feature/core-models.

Files added
- frontend/src/components/accounting/DisburseModal.jsx — Disburse preview & confirm modal
- frontend/src/components/accounting/RepayModal.jsx — Repayment preview & confirm modal
- frontend/src/components/accounting/PreviewTable.jsx — renders postings preview table
- frontend/src/components/accounting/api.js — small helpers to call preview & execute endpoints
- frontend/src/components/accounting/styles.css — basic styling
- frontend/src/components/accounting/utils.js — small formatter

How to use
1. Ensure your frontend app serves these components (import them in your loan detail page). Example usage in a React page:

```jsx
import React, { useState } from 'react';
import DisburseModal from '../components/accounting/DisburseModal';
import RepayModal from '../components/accounting/RepayModal';

function LoanDetail({ applicationNumber, token }) {
  const [showDisburse, setShowDisburse] = useState(false);
  const [showRepay, setShowRepay] = useState(false);

  return (
    <div>
      <h1>Loan {applicationNumber}</h1>
      <button onClick={() => setShowDisburse(true)}>Disburse</button>
      <button onClick={() => setShowRepay(true)}>Repay</button>

      <DisburseModal
        applicationNumber={applicationNumber}
        visible={showDisburse}
        onClose={() => setShowDisburse(false)}
        token={token}
        onSuccess={(res) => window.alert('Disbursed: ' + JSON.stringify(res))}
      />

      <RepayModal
        applicationNumber={applicationNumber}
        visible={showRepay}
        onClose={() => setShowRepay(false)}
        token={token}
        onSuccess={(res) => window.alert('Repayment posted: ' + JSON.stringify(res))}
      />
    </div>
  );
}
```

2. Authentication
- The components accept a `token` prop and will set an Authorization header `Token <token>` when present. Adjust if your frontend uses a different auth method (JWT, session cookie).

3. Backend endpoints
- Disburse preview: POST /api/loans/{application_number}/disburse/?preview=true
- Disburse execute: POST /api/loans/{application_number}/disburse/
- Repay preview: POST /api/loans/{application_number}/repay/?preview=true
- Repay execute: POST /api/loans/{application_number}/repay/

4. Tests
- Add unit tests for the components and integration tests that mock the API responses.

Notes & next steps
- The modal UI is intentionally minimal; feel free to wire into your design system (Material UI, Bootstrap, etc.)
- I can add TypeScript typings, Storybook stories, or E2E Playwright/Cypress tests on request.
