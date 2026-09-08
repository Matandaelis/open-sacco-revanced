import React, { useState } from 'react';
import PreviewTable from './PreviewTable';
import { postPreview, postExecute } from './api';
import './styles.css';

export default function RepayModal({ applicationNumber, visible, onClose, token, onSuccess }) {
  const [installmentNumber, setInstallmentNumber] = useState(1);
  const [accountNumber, setAccountNumber] = useState('');
  const [narration, setNarration] = useState('');
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!visible) return null;

  async function handlePreview() {
    setError(null);
    setLoading(true);
    try {
      const url = `/api/loans/${applicationNumber}/repay/`;
      const body = { account_number: accountNumber, installment_number: installmentNumber, narration };
      const json = await postPreview(url, body, token);
      setPreview(json.preview || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm() {
    setError(null);
    setLoading(true);
    try {
      const url = `/api/loans/${applicationNumber}/repay/`;
      const body = { account_number: accountNumber, installment_number: installmentNumber, narration };
      const res = await postExecute(url, body, token);
      if (onSuccess) onSuccess(res);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Repay Installment — Preview</h3>
        <label>
          Installment number
          <input type="number" value={installmentNumber} onChange={(e) => setInstallmentNumber(parseInt(e.target.value, 10))} />
        </label>
        <label>
          Account number
          <input value={accountNumber} onChange={(e) => setAccountNumber(e.target.value)} />
        </label>
        <label>
          Narration
          <textarea value={narration} onChange={(e) => setNarration(e.target.value)} />
        </label>
        <div className="modal-actions">
          <button onClick={handlePreview} disabled={loading || !accountNumber}>Preview</button>
          <button onClick={onClose} className="muted">Close</button>
        </div>
        {loading && <div>Loading…</div>}
        {error && <div className="error">{error}</div>}
        {preview && <PreviewTable postings={preview} />}
        {preview && Math.abs((preview.filter(p=>p.entry_type==='debit').reduce((s,p)=>s+parseFloat(p.amount),0)) - (preview.filter(p=>p.entry_type==='credit').reduce((s,p)=>s+parseFloat(p.amount),0))) < 0.001 && (
          <div className="modal-actions">
            <button onClick={handleConfirm} disabled={loading}>Confirm Repayment</button>
          </div>
        )}
      </div>
    </div>
  );
}
