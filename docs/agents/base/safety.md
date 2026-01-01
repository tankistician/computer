# Safety + Security Guardrails

## Secrets
- Never print, store, or request real secrets in plain text.
- Use env vars / secret managers / injected runtime credentials.

## Injection
- Treat user-provided strings as untrusted:
  - SQL: parameterize, whitelist identifiers.
  - Shell: avoid string concatenation; use args arrays.
  - HTTP: validate URLs, methods, headers.

## Data handling
- Minimize data returned. Use LIMIT or sampling for large datasets.
- Redact PII when possible.
- Prefer aggregated results unless raw rows are needed.

## Permissions
- Use least privilege:
  - DB users read-only for query agents.
  - Separate roles per environment (dev/stage/prod).
