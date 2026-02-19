# Security Policy

## Reporting a Vulnerability

Please do not open public GitHub issues for security vulnerabilities.

Report privately by email:
- `security@foretokenai.com`

Include:
- Affected component/file
- Reproduction steps
- Potential impact
- Suggested mitigation (if known)

## Scope

This policy applies to the open-source InterviewOS repository.

## Secrets Handling

- Never commit `.env` files or cloud credentials.
- Use `.env.example` for configuration templates.
- Rotate any credential immediately if it is accidentally exposed.
