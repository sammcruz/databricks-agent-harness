---
date: 2026-11-27 12:02
area: environment-setup
status: open
seen: 1
---

# Authentication verification output included account identity

- Symptom: A filtered `gh auth status` check printed the authenticated account name despite the request not to show login details.
- Cause: The output filter selected the full “Logged in to ... account” line instead of checking only authentication success and scopes.
- Fix: Avoid printing identity-bearing status lines; verify success and required scopes without echoing account details.
- Prevention: Update `skills/core/environment-setup/SKILL.md` to document identity-safe authentication verification.
