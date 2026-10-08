# UC-06 — Build the Fund Transfer service with Copilot

**Day 3 · Module: GitHub Copilot (part 1) · Slot: 2 hrs · Demo: 25 min**

## Goal

Use Copilot to write the Fund Transfer logic from the spec. Show that **good context and repository instructions give better code**, then refactor and add tests.

## Time plan (120 min)

| Time        | Activity                                                                      |
| ----------- | ----------------------------------------------------------------------------- |
| 0–45 min    | Concepts (good prompts, giving context, custom instructions, common mistakes) |
| 45–70 min   | Demo (25 min)                                                                 |
| 70–110 min  | Hands-on (Stage 1: build, Stage 2: refactor + test)                           |
| 110–120 min | Discussion                                                                    |

## Before the session

`simple-bank` project with the Fund Transfer spec, plan and tasks (from UC-02/03), and an empty FastAPI project.

---

## Demo

### Step 1 — No context vs with context (5 min)

In Copilot Chat (Agent mode), with no files attached:

```text
Write fund transfer logic.
```

Show the result: made-up rules, `float` for money, no daily limit. Undo it.

Now with context:

```text
Write the fund transfer logic from #file:specs/001-fund-transfer/spec.md
using the entities in #file:specs/001-fund-transfer/data-model.md .
```

Show how much closer it is. Undo again — next we add instructions.

### Step 2 — Review repository instructions (5 min)

Open `.github/copilot-instructions.md` and discuss how repository-wide guidance can improve Copilot's responses. The file already contains general Simple Bank guidance; add or adapt rules for the active use case as needed. For example:

```markdown
# Simple Bank - Copilot instructions

- Python 3.12, FastAPI.
- Use Decimal for money. Round to 2 decimals.
- Never log full account numbers. Mask them like XXXX1234.
- Never put passwords or keys in code.
- Error responses use clear error codes, e.g. INSUFFICIENT_BALANCE.
- Write pytest tests for every rule. Test names should describe the rule.
```

Note to Trainees: _"Copilot reads this file automatically for every chat in this repo."_

### Step 3 — Stage 1: write the code (7 min)

```text
Using #file:specs/001-fund-transfer/spec.md , create a TransferService class with
a transfer(from_account, to_account, amount) method that applies all the rules
(amount > 0, enough balance, daily limit, not same account, both accounts active).
Return a result with a transaction ID or an error code. Keep it free of FastAPI so it is easy to test.
```

Review with the class:

- Is `Decimal` used?
- Is the daily limit check `<=` Rs 1,00,000 (not `<`)?
- Is the new-account limit (Rs 50,000) from UC-03 included?

If something is wrong, select the code and press **Ctrl+I** (inline chat):

```text
The daily limit check should allow exactly Rs 1,00,000. Fix only this.
```

### Step 4 — Stage 2: refactor (4 min)

Select the `transfer` method, press **Ctrl+I**:

```text
Refactor this: extract each rule into its own small `_`-prefixed method with a clear name.
Do not change the behaviour.
```

### Step 5 — Stage 2: tests (4 min)

```text
Write pytest tests for TransferService: one test for each acceptance criterion in
#file:specs/001-fund-transfer/spec.md . Then list each acceptance criterion and the test that covers it.
```

Run the tests (`uv run pytest`). Point out: **every rule in the spec should have a test** — if not, something is missing.

---

## Common mistakes (show at the end)

| Mistake                   | Example today                    | Fix                            |
| ------------------------- | -------------------------------- | ------------------------------ |
| Not enough context        | "Write fund transfer logic"      | Attach the spec with `#file`   |
| Too long a prompt         | Copying the whole spec into chat | Point to the spec file instead |
| Accepting without reading | Limit check using `<`            | Review against the rules       |

## Hands-on (40 min)

Using your own spec from UC-02:

1. Add a `.github/copilot-instructions.md` with at least 4 rules.
2. **Stage 1:** ask Copilot to write the logic using your spec as context.
3. **Stage 2:** refactor one method with inline chat and generate tests.
4. Check: does every acceptance criterion have a test?

## Discussion questions

- What changed after adding the instructions file?
- Did Copilot get any rule wrong? How did you find it?
