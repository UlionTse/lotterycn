# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.0.0 | ✅ |
| < 1.0.0 | ❌ |

## Reporting a Vulnerability

Please report security issues **privately** by email to **shinalone@outlook.com** rather than opening a public issue. Include a description of the issue, the steps to reproduce it, and the affected version. You can expect an initial response within 7 days.

## Scope Notes

LotteryCN is a client library that only **reads** public draw data from official lottery websites (`cwl.gov.cn`, `lottery.gov.cn`). It:

- does not handle user credentials, payment data, or personal information;
- writes only local cache files under the user's own home directory (or an explicitly configured `cache_dir`);
- never executes code fetched from remote responses.

Reports about upstream website availability or scraping ethics are out of scope for security policy but are welcome as regular issues.
