# AI-Written Code Review Checklist (Bank)

**Rule:** AI writes the code; a named human owns it. Nothing ships on AI output alone.

**Who checks:** **Dev** = author using the AI · **Reviewer** = peer who did not write it · **Lead** = tech lead · **Security** = AppSec · **QA** = tester · **Risk** = compliance/risk · **Release** = release manager

## 1. Before coding

| Done | Check | Who |
|------|-------|-----|
| [ ] | Spec and acceptance criteria are written and approved | Lead |
| [ ] | AI tool is on the bank's approved list | Security |
| [ ] | No customer data, account numbers or secrets are pasted into prompts | Dev |
| [ ] | Prompt names the stack, money rules (`Decimal`) and error-code format | Dev |
| [ ] | Work is on a new branch, not `main` | Dev |

## 2. Code review

| Done | Check | Who |
|------|-------|-----|
| [ ] | Dev can explain every line; no code is kept that nobody understands | Dev |
| [ ] | Code matches the spec; no extra business rules or features added | Reviewer |
| [ ] | Money uses `Decimal`, never `float` | Reviewer |
| [ ] | Transfer rules intact: positive amount, enough balance, daily limit, different active accounts, unique transaction ID | Reviewer |
| [ ] | Every library exists, is approved and pinned (AI can invent packages) | Reviewer |
| [ ] | No dead, duplicated or copied code with an unknown licence | Reviewer |
| [ ] | Errors return stable codes and never expose internal details | Reviewer |

## 3. Security checks

| Done | Check | Who |
|------|-------|-----|
| [ ] | No hard-coded credentials, keys or tokens (secret scan passes) | Security |
| [ ] | All inputs validated; queries parameterised (no SQL injection) | Security |
| [ ] | Authentication and authorisation on every endpoint | Security |
| [ ] | Logs mask account numbers and hold no customer data | Reviewer |
| [ ] | Dependency and static analysis scans show no high or critical issues | Security |
| [ ] | Audit trail records who did what on money movements | Risk |

## 4. Testing

| Done | Check | Who |
|------|-------|-----|
| [ ] | Each acceptance criterion has an automated test | Dev |
| [ ] | Tests cover failures: zero, negative, over-limit, same account, inactive account | QA |
| [ ] | Tests were checked by a human, not just generated and passed | Reviewer |
| [ ] | Rounding and duplicate-transaction cases tested | QA |
| [ ] | Full test suite passes in CI | Dev |

## 5. Before release

| Done | Check | Who |
|------|-------|-----|
| [ ] | Reviewer approved the pull request; AI use is noted in it | Reviewer |
| [ ] | Change was tested in a staging environment | QA |
| [ ] | Compliance and risk sign-off recorded | Risk |
| [ ] | Rollback plan exists and has been tried | Release |
| [ ] | Monitoring and alerts are in place for the change | Release |

**Sign-off:** Dev ________ Reviewer ________ Security ________ QA ________ Release ________ Date ________
