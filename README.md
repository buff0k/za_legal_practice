# ZA Legal Practice

A South African legal practice management application built on Frappe and ERPNext.

The app extends ERPNext with legal-practice setup, attorney profiles, matter configuration, practice areas, practice branches, matter types, and trust-account configuration using ERPNext's existing `Bank Account` functionality.

## Repository

```text
https://github.com/buff0k/za_legal_practice
```

Current working branch:

```text
version-16
```

## Required dependencies

This app is built for the Frappe / ERPNext v16 stack.

Required:

- Frappe Framework v16
- ERPNext v16
- Bench CLI

Not required by default:

- HRMS / Frappe HR

HRMS support is optional. Attorney records are based on `User` and `Attorney Profile`. Linking to `Employee` is only enabled where HRMS is installed and configured.

## Current status

The current development focus is the legal-practice foundation layer, especially Practice Setup and trust-account configuration.

Implemented or in progress:

- `Legal Practice Settings` singleton for firm-wide legal-practice defaults.
- `Attorney Profile` master linked to Frappe `User`.
- `Attorney Trust Account Access` child table for restricting attorneys to trust accounts.
- `Practice Area` setup DocType for broad legal work categories.
- `Practice Branch` setup DocType as a legal-practice wrapper around ERPNext `Branch`.
- `Matter Type` setup DocType for operational matter defaults.
- Matter Type child tables for:
  - required documents;
  - checklist items;
  - default tasks;
  - billing items.
- Legal trust-account custom fields on ERPNext `Bank Account` using the `za_lp_` custom-field prefix.
- Trust Account terminology aligned to South African legal-practice requirements.

Important design decision:

```text
Trust Account = ERPNext Bank Account
```

The app does not create a separate `Trust Fund` DocType. Trust-account metadata is added to ERPNext `Bank Account` through custom fields.

## Planned work

Planned setup and operational DocTypes include:

- Matter Stage.
- Legal Party Role.
- Court / Forum.
- Compliance Requirement Type.
- Legal Document Template.
- Legal Client.
- Matter.
- Matter Party.
- Matter Team.
- Matter checklist and task generation.
- Trust Receipt.
- Trust Payment.
- Trust Transfer to Business.
- Trust Reconciliation.
- Matter billing and disbursement recovery.
- Reports for trust accounting, matters, billing, and compliance.

Future / deferred:

- Legal publishing / Acts module.
- Client portal features.
- Optional HRMS integration.

## Installation

Install the app using the [bench](https://github.com/frappe/bench) CLI.

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/buff0k/za_legal_practice --branch version-16
bench install-app za_legal_practice
```

If ERPNext is not already installed on the site, install ERPNext first.

```bash
bench get-app erpnext --branch version-16
bench --site your-site.local install-app erpnext
bench --site your-site.local install-app za_legal_practice
```

Then run:

```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
```

## Initial setup

After installing the app, configure the foundation in this order:

1. Open `Legal Practice Settings`.
2. Set the default company, business bank account, trust-account controls, naming series, and compliance defaults.
3. Mark the required ERPNext `Bank Account` records as legal trust accounts.
4. Complete the trust-account custom fields on each trust account:
   - `za_lp_is_legal_trust_account`
   - `za_lp_trust_account_type`
   - `za_lp_trust_account_active`
   - `za_lp_trust_creditor_account`
   - `za_lp_requires_dual_approval`
   - `za_lp_require_matter_dimension`
   - `za_lp_block_manual_posting`
5. Create `Attorney Profile` records and link them to Frappe users.
6. Add permitted trust accounts in the `Attorney Trust Account Access` child table.
7. Create `Practice Branch` records.
8. Create `Practice Area` records.
9. Create `Matter Type` records.

## Trust Account filters

Where a DocType has a field named `default_trust_account` or `trust_account`, the field should link to ERPNext `Bank Account` and should be filtered to legal trust accounts only:

```json
[
  ["Bank Account", "za_lp_is_legal_trust_account", "=", 1],
  ["Bank Account", "za_lp_trust_account_active", "=", 1]
]
```

This applies to the trust-account link fields on:

- `Legal Practice Settings`
- `Attorney Profile`
- `Attorney Trust Account Access`
- `Practice Area`
- `Practice Branch`
- `Matter Type`
- future `Matter` and trust transaction DocTypes

Business bank account fields should not use this filter.

## Fixtures

The app uses fixtures for custom fields added to standard ERPNext DocTypes.

Current fixture focus:

```text
za_legal_practice/fixtures/custom_fields.json
```

The Bank Account custom fields use the `za_lp_` prefix and are exported by deterministic Custom Field names such as:

```text
Bank Account-za_lp_is_legal_trust_account
Bank Account-za_lp_trust_creditor_account
```

The recommended `hooks.py` fixture filter style is by `name`, not only by `dt` and `fieldname`, so that only the intended app-owned custom fields are exported.

Example:

```python
fixtures = [
    {"dt": "Custom Field", "filters": [["name", "in",[
        "Bank Account-za_lp_legal_trust_account_section",
        "Bank Account-za_lp_is_legal_trust_account",
        "Bank Account-za_lp_trust_account_type",
        "Bank Account-za_lp_trust_account_active",
        "Bank Account-za_lp_trust_controls_column_break",
        "Bank Account-za_lp_requires_dual_approval",
        "Bank Account-za_lp_require_matter_dimension",
        "Bank Account-za_lp_block_manual_posting",
        "Bank Account-za_lp_trust_accounting_accounts_section",
        "Bank Account-za_lp_trust_creditor_account",
        "Bank Account-za_lp_trust_investment_account",
        "Bank Account-za_lp_lpff_interest_account",
        "Bank Account-za_lp_trust_accounts_column_break",
        "Bank Account-za_lp_trust_bank_charges_account",
        "Bank Account-za_lp_trust_rounding_difference_account",
        "Bank Account-za_lp_trust_account_ownership_section",
        "Bank Account-za_lp_responsible_attorney",
        "Bank Account-za_lp_practice_branch",
        "Bank Account-za_lp_practice_area",
        "Bank Account-za_lp_trust_notes_column_break",
        "Bank Account-za_lp_trust_account_notes"
    ]]]}
]
```

After changing fixtures, run:

```bash
bench --site your-site.local export-fixtures
bench --site your-site.local migrate
bench --site your-site.local clear-cache
```

## Development notes

This repository is currently focused on Frappe / ERPNext v16.

General development flow:

```bash
cd $PATH_TO_YOUR_BENCH/apps/za_legal_practice
```

After changing DocTypes, fixtures, hooks, or Python controllers, run:

```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
bench restart
```

When adding custom fields to standard ERPNext DocTypes, use the `za_lp_` fieldname prefix.

When adding fields to app-owned DocTypes, the `za_lp_` prefix is not required unless there is a specific collision risk.

## License

MIT