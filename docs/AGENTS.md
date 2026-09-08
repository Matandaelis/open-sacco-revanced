# Agents README

This document describes the "agents" (automations, management commands, admin actions, and helpers) added to the project to help migrate legacy ledger data, create/reverse journals, and integrate double-entry accounting into the app.

Agents and tools included

- migrate_ledger (management command)
  - Path: backend/accounting/management/commands/migrate_ledger.py
  - Purpose: Dry-run and apply migration of legacy groups.LedgerEntry rows into accounting.JournalEntry + Posting records.
  - Modes: --dry-run (default), --apply, --limit N
  - Safety: Uses MigrationRecord to avoid double-migration; supports small-batch apply.

- reverse_journal (management command)
  - Path: backend/accounting/management/commands/reverse_journal.py
  - Purpose: Create reversing JournalEntry rows for a list of JournalEntry IDs. Used for safe undo of posted journals.
  - Usage: python manage.py reverse_journal --journal-ids <id1,id2> --reason "text"

- Admin action: Create reversal journals
  - Registered on Accounting → Journal entries admin.
  - Purpose: UI action to create reversing journals for selected JournalEntry rows.

- MigrationRecord model
  - Path: backend/accounting/models.py
  - Purpose: Tracks legacy ledger rows already migrated to prevent duplicates and provide an audit link.

- post_journal service
  - Path: backend/accounting/services.py
  - Purpose: Canonical helper to create JournalEntry + Posting rows from posting definitions. Validates balancing and computes running balance_after.

How to use these agents safely

1. Always run migrate_ledger in --dry-run mode first (use --limit small) and review the JSON preview.
2. Apply migration in small batches (--apply --limit 25) and inspect created JournalEntry rows in admin.
3. If a migration apply has a problem, use reverse_journal on the created JournalEntry IDs, or restore DB snapshot if available.
4. After migration, review MigrationRecord entries to confirm all legacy rows were processed.

Operational notes

- The migrate_ledger command will skip legacy rows that already have a MigrationRecord.
- The post_journal service is the single place to create journals programmatically — other code paths should call it rather than creating JournalEntry/Postings directly.
- The reverse_journal command and admin action create reversal journals (they do not delete or mutate the original journals).

Contact

If you need changes to mapping heuristics, additional logs, or batch orchestration scripts, reach out to the engineering owner or raise an issue in the repository.
