# Security Policy

## Supported Versions

Security fixes are applied to the latest version on the default development
branch and the active pre-production branch.

## Reporting a Vulnerability

Please do not report security vulnerabilities in a public issue. Use GitHub's
private security advisory reporting for this repository:

<https://github.com/anujbankar2503/Enterprise_Employee_Analytics_Data_Warehouse_System/security/advisories/new>

Include the affected file or component, reproduction steps, impact, and any
suggested mitigation. Do not include passwords, API keys, database dumps, or
other secrets in a report.

You should receive an acknowledgement within five business days. We will
coordinate validation, remediation, and disclosure with the reporter.

## Handling Secrets

- Keep `app/.env` and Streamlit secrets out of Git.
- Rotate credentials immediately if they are exposed.
- Use least-privilege MySQL accounts for local and deployed environments.
- Avoid placing private employee data in issues, logs, screenshots, or commits.
