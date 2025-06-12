# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing security@omnex.ai

**Do not report security vulnerabilities through public GitHub issues.**

### What to Include

* Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the issue
* Location of affected source code (tag/branch/commit or direct URL)
* Step-by-step instructions to reproduce the issue
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit it

### Response Timeline

* **Initial response**: within 48 hours
* **Status update**: within 7 days
* **Resolution timeline**: depends on severity
  - Critical: 7-14 days
  - High: 14-30 days
  - Medium: 30-60 days
  - Low: 60-90 days

### Disclosure Policy

We follow Coordinated Vulnerability Disclosure (CVD) practices:

1. Security issues are fixed in private
2. We prepare security advisories and patches
3. We notify affected users (if applicable)
4. We release patches
5. We publicly disclose the vulnerability details

## Security Best Practices

When contributing to Omnex:

1. **Never commit secrets**: API keys, passwords, tokens, etc.
2. **Validate all inputs**: Prevent injection attacks
3. **Use parameterized queries**: Prevent SQL injection
4. **Implement proper authentication**: Use JWT tokens correctly
5. **Follow OWASP guidelines**: For web security best practices

## Security Features

Omnex implements several security measures:

- JWT-based authentication
- Rate limiting
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
- CORS configuration
- Environment-based secrets management
- Encrypted password storage with bcrypt

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who help us maintain Omnex's security.