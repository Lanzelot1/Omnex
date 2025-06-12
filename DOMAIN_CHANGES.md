# Domain Reference Removal Summary

All references to the `omnex.ai` domain have been successfully removed from the project.

## Changes Made:

### 1. **README.md**
- Discord link changed from `https://discord.gg/omnex` to `#` (placeholder)
- Documentation links changed from `https://docs.omnex.ai/*` to local `docs/` paths

### 2. **CODE_OF_CONDUCT.md**
- Email `conduct@omnex.ai` → "through GitHub issues or discussions"

### 3. **CONTRIBUTING.md**
- Documentation link `https://docs.omnex.ai` → `./docs/`
- Discord link removed, replaced with "Join our community discussions"

### 4. **SECURITY.md**
- Email `security@omnex.ai` → "creating a private security advisory on GitHub"

### 5. **pyproject.toml**
- Removed email addresses from authors and maintainers
- Removed Homepage URL
- Documentation URL now points to GitHub repo docs

### 6. **package.json**
- Homepage changed from `https://omnex.ai` to GitHub repository

### 7. **src/__init__.py**
- Removed `__email__` field

### 8. **CITATION.cff**
- Removed email from authors
- Removed url field pointing to omnex.ai

### 9. **.github/ISSUE_TEMPLATE/config.yml**
- Security email changed to GitHub security advisories URL

## Recommendation:
When you acquire a domain, you can easily update these references by searching for:
- GitHub repository URLs
- Email placeholders
- Documentation links

All functionality remains intact, and the project now uses GitHub-based alternatives for all external references.