import React from 'react';
import './styles.css';
import { formatMoney } from './utils';

export default function PreviewTable({ postings = [] }) {
  const totalDebit = postings
    .filter((p) => p.entry_type === 'debit')
    .reduce((s, p) => s + parseFloat(p.amount), 0);
  const totalCredit = postings
    .filter((p) => p.entry_type === 'credit')
    .reduce((s, p) => s + parseFloat(p.amount), 0);

  return (
    <div className="preview-table">
      <table>
        <thead>
          <tr>
            <th>Account</th>
            <th>Type</th>
            <th className="right">Amount</th>
          </tr>
        </thead>
        <tbody>
          {postings.map((p) => (
            <tr key={`${p.account_code}-${p.entry_type}-${p.amount}`}>
              <td>{p.account_name || p.account_code}</td>
              <td>{p.entry_type}</td>
              <td className="right">{formatMoney(p.amount)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="totals">
            <td colSpan={1}>Totals</td>
            <td>Debit {formatMoney(totalDebit)}</td>
            <td className="right">Credit {formatMoney(totalCredit)}</td>
          </tr>
        </tfoot>
      </table>
      <div className={`balance-indicator ${Math.abs(totalDebit - totalCredit) < 0.001 ? 'balanced' : 'unbalanced'}`}>
        {Math.abs(totalDebit - totalCredit) < 0.001 ? 'Balanced' : `Unbalanced (Δ ${formatMoney(totalDebit - totalCredit)})`}
      </div>
    </div>
  );
}
