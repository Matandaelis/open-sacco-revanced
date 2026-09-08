import React from 'react';

export function formatMoney(amount) {
  try {
    return parseFloat(amount).toFixed(2);
  } catch (e) {
    return amount;
  }
}
