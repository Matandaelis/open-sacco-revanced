import React from 'react';
import ReactDOM from 'react-dom/client';
import LoanDetailIntegration from './pages/LoanDetailIntegration';
import './components/accounting/styles.css';

// Look for an element with id 'loan-detail-root' and mount the LoanDetailIntegration React component
// Expected attributes on the element:
// - data-application-number="APP-000123"
// - data-token="<auth-token>" (optional)
// - data-user='{ "is_staff": true, "roles": ["loan", "finance"] }' (JSON string)

const rootEl = document.getElementById('loan-detail-root');
if (rootEl) {
  try {
    const applicationNumber = rootEl.getAttribute('data-application-number');
    const token = rootEl.getAttribute('data-token') || null;
    const userAttr = rootEl.getAttribute('data-user');
    let user = null;
    if (userAttr) {
      try {
        user = JSON.parse(userAttr);
      } catch (err) {
        console.warn('Failed to parse data-user JSON on loan-detail-root', err);
      }
    }

    const root = ReactDOM.createRoot(rootEl);
    root.render(
      React.createElement(LoanDetailIntegration, { applicationNumber, token, user })
    );
  } catch (err) {
    // ensure mounting errors don't break the host page
    // eslint-disable-next-line no-console
    console.error('Failed to mount LoanDetailIntegration:', err);
  }
}
