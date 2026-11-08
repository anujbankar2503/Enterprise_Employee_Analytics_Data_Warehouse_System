# Contributing

Thank you for contributing to Enterprise Employee Analytics.

## Before You Start

1. Check existing issues and pull requests.
2. Open an issue for significant behavior or schema changes.
3. Never commit `app/.env`, credentials, employee data, or generated CSV files.

## Local Setup

Follow the setup instructions in [README.md](README.md). Install the Python
dependencies, configure MySQL, and provide the required HR source CSV locally.

## Making Changes

- Keep changes focused and preserve existing manager and entity contracts.
- Put database access in the DAL rather than directly in Streamlit pages.
- Keep user-facing text clear for HR users; avoid exposing SQL or warehouse jargon.
- Add or update focused validation for changed behavior.
- Update SQL documentation when table or procedure contracts change.

## Validation

Run the following before opening a pull request:

```powershell
py -3 -m compileall -q app src
```

Run relevant diagnostic scripts when their CSV and database prerequisites are
available.

## Pull Requests

A pull request should include:

- A concise summary of the change.
- The user-visible or database behavior affected.
- Validation commands and results.
- Notes about migrations, environment variables, or manual setup.

Keep pull requests reviewable and do not include unrelated formatting changes.
