import React, { useState } from 'react';
import DisburseModal from '../components/accounting/DisburseModal';
import RepayModal from '../components/accounting/RepayModal';

// Example loan detail integration page that wires the preview modals into the UI.
// Adapt this to your routing and data-fetching approach (hooks, Redux, etc.).

export default function LoanDetailIntegration({ applicationNumber, token, user }) {
  const [showDisburse, setShowDisburse] = useState(false);
  const [showRepay, setShowRepay] = useState(false);

  // Simple role check - adapt to your app's permission model
  const isLoanOfficer = user && (user.is_staff || (user.roles && user.roles.includes('loan')));
  const isFinance = user && (user.is_staff || (user.roles && user.roles.includes('finance')));

  return (
    <div style={{ padding: 16 }}>
      <h2>Loan {applicationNumber}</h2>
      <div style={{ display: 'flex', gap: 8 }}>
        {isLoanOfficer && <button onClick={() => setShowDisburse(true)}>Disburse</button>}
        {isLoanOfficer && <button onClick={() => setShowRepay(true)}>Repay</button>}
      </div>

      <DisburseModal
        applicationNumber={applicationNumber}
        visible={showDisburse}
        onClose={() => setShowDisburse(false)}
        token={token}
        onSuccess={(res) => {
          // you probably want to refresh loan data here
          window.alert('Disbursement completed')
        }}
      />

      <RepayModal
        applicationNumber={applicationNumber}
        visible={showRepay}
        onClose={() => setShowRepay(false)}
        token={token}
        onSuccess={(res) => {
          // refresh loan data / UI
          window.alert('Repayment posted')
        }}
      />
    </div>
  );
}
