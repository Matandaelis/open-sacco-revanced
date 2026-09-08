# Accounting Integration Checklist

This checklist summarizes what has been completed and the planned next steps to fully integrate the double-entry accounting system. Use this during staging and production rollout.

Completed (Already implemented on branch feature/core-models)

- Backend accounting models
  - [x] Account model (chart of accounts)
  - [x] JournalEntry model with GenericForeignKey to source objects
  - [x] Posting model with balance_after caching
  - [x] MigrationRecord model to track migrated legacy rows

- Services
  - [x] post_journal(...) service that validates balanced postings and writes JournalEntry + Postings
  - [x] create_group_accounts and create_member_accounts helpers

- Domain wiring
  - [x] Create group and member accounts on group/member creation (non-blocking)
  - [x] Contribution.save posts a Journal (debit group cash, credit member savings) with legacy fallback
  - [x] Loan disbursement & repayment flows wired to post_journal with legacy fallback

- Migration tooling
  - [x] migrate_ledger management command (dry-run + apply + limit)
  - [x] Mapping heuristics for contributions, loan disbursements and repayments
  - [x] MigrationRecord integration to make migration idempotent

- Reversals & admin
  - [x] Admin action to create reversal journals for selected JournalEntry rows
  - [x] reverse_journal management command to create reversing journals
  - [x] MigrationRecord visible in admin

- Preview & UI integration
  - [x] Loan endpoints support preview mode for disburse and repay
  - [x] Accounting read API endpoints (accounts, journals)
  - [x] React preview UI for Disburse & Repay (modals, preview table, API helpers)


Current short-term tasks (should be done next)

- [ ] Wire DisburseModal & RepayModal into production loan detail pages (frontend integration)
- [ ] Add role-based UI guard (hide/disable Confirm for unauthorized users) — frontend
- [ ] Add backend unit tests for preview and execute flows (disburse/repay)
- [ ] Add integration tests for the end-to-end flows and migration idempotence
- [ ] Add frontend unit tests and an E2E test (Cypress/Playwright) for preview -> confirm

Mid-term tasks (after preview + small-batch migration validated)

- [ ] Run full migration in controlled batches on staging; validate trial balance after each batch
- [ ] Implement a Migration Dashboard (admin) that shows dry-run JSON, enables apply in batches, and shows progress
- [ ] Add marker/archival on legacy LedgerEntry (optional) after successful migration
- [ ] Implement reversal UI (modal + API) to enable finance to reverse journals with approver workflow
- [ ] Add manual journal creation API for finance/admins (through post_journal)

Long-term tasks (post-migration)

- [ ] Reports (Trial Balance, Balance Sheet, Income Statement, Member Statement, Group Cashbook)
- [ ] Shareout flows, penalties, and complex accounting events (allocated journals + reports)
- [ ] Performance tuning for large numbers of postings and reports (indexes, caching)
- [ ] Analytics & monitoring (trial-balance checks, alerts on discrepancies)
- [ ] Documentation & runbooks for finance team (how to preview/execute/reverse/migrate)

Acceptance criteria for rollout

- All legacy LedgerEntry rows are migrated and recorded in MigrationRecord or flagged for manual reconciliation.
- Core flows (contribution/disburse/repay) consistently create balanced JournalEntry/Postings and link to domain objects.
- Reports yield correct trial balance and financial statements for a sample set of groups.
- UI previews match executed journals exactly and allow finance users to confirm before executing.
- Tests (unit + integration) pass in CI.

Notes & risks

- Always take a DB snapshot before running --apply on production.
- The current mapping heuristics attempt to split repayment into principal/interest when transaction fields exist; manual reconciliation may be required for ambiguous legacy rows.
- The migration command creates journals but does not modify or delete legacy LedgerEntry rows; MigrationRecord prevents double-processing.

