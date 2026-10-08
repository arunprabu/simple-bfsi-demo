# UC-11 — Review an AI-written Customer Search API

**Day 6 (Week 2) · Module: Governance — Validation & Security · Slot: 2 hrs · Demo: 25 min**

## Goal

Show that AI-written code can look fine but still have security problems. Find them using a **SAST scan**, **Copilot review**, and **a human reviewer**, then create a simple review checklist.

## Time plan (120 min)

| Time        | Activity                                                                                       |
| ----------- | ---------------------------------------------------------------------------------------------- |
| 0–45 min    | Concepts (checking AI code, common security issues, data privacy, human review, company rules) |
| 45–70 min   | Demo (25 min)                                                                                  |
| 70–110 min  | Hands-on                                                                                       |
| 110–120 min | Discussion                                                                                     |

## Before the session

- Add this file to the repo as `review/customer_search.py` and push it **a day before** so CodeQL has time to scan it.
- Install Semgrep: `pip install semgrep`.

```python
import pymysql
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

DB_PASSWORD = "Bank@123"

def get_connection():
    return pymysql.connect(host="localhost", user="admin",
                           password=DB_PASSWORD, database="bank")

@app.get("/api/v1/customers/search")
def search(name: str):
    con = get_connection()
    cur = con.cursor()
    sql = "SELECT * FROM customer WHERE name LIKE '%" + name + "%'"
    cur.execute(sql)
    columns = [col[0] for col in cur.description]
    result = [dict(zip(columns, row)) for row in cur.fetchall()]
    for customer in result:
        print(f"Found customer {customer.get('name')} account {customer.get('account_number')}")
    return result

@app.exception_handler(Exception)
async def error(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Error: " + str(exc)})
```

**Answer key (for you):**
| # | Problem | Why it matters |
|---|---|---|
| 1 | SQL built by joining strings | SQL injection — attacker can read the whole table |
| 2 | Hard-coded password | Anyone who sees the code knows it |
| 3 | Full account number and name printed | Sensitive customer data in logs |
| 4 | `SELECT *` returns every column | Sends data the screen doesn't need (PAN, date of birth…) |
| 5 | Error message shows internal details | Helps attackers learn about the system |
| 6 | No check on who is calling | Anyone can search all customers |

---

## Demo

### Step 1 — Quick look (2 min)

Show the code. Ask: _"Would you approve this PR?"_ Most people spot 1 or 2 problems.

### Step 2 — SAST scan (5 min)

```bash
semgrep scan --config p/python --config p/secrets review/
```

Then show **GitHub → Security → Code scanning** for the CodeQL results.
Count: which problems did the tools find? Usually #1 and #2. They often miss #3, #4 and #6.

### Step 3 — Copilot review (6 min)

Copilot Chat (Ask mode):

```text
Review #file:review/customer_search.py as a bank security reviewer.
Find security problems, customer data privacy problems, and bad practices.
Show a table: Problem | Line | Severity (High/Medium/Low) | How to fix.
Also tell me what you cannot check from this file alone.
```

Compare with the scan results.

### Step 4 — What the human finds (3 min)

Point to #6: there's no check on **who** is calling. Any user could search every customer in the bank. Tools don't know the business rule "only branch staff can search customers" — a person does.

### Step 5 — Fix with Copilot and scan again (5 min)

Agent mode:

```text
Fix the problems in #file:review/customer_search.py :
use a parameterised query, remove the hard-coded password, select only id, name and masked account number,
do not print customer data, return a simple error message without internal details,
and allow only users with the role BRANCH_STAFF.
```

Run Semgrep again. Note to Trainees: _"The fix is also AI-written, so it needs review too."_

### Step 6 — Simple review checklist (4 min)

```text
Create a one-page checklist for reviewing AI-written code in a bank. Keep it simple, with sections:
Before coding, Code review, Security checks, Testing, Before release.
Each item should say who checks it.
```

Tidy it up with the class. Save as `docs/ai-review-checklist.md` — it is used in the case studies (UC-12).

---

## Hands-on (40 min)

1. Run Semgrep and the Copilot review prompt on **your own code** from UC-06, UC-08, and UC-10.
2. Make a table: what the scan found, what Copilot found, what you found yourself.
3. Fix the top 2 problems and scan again.
4. Add one item to the checklist that's specific to your feature.

## Discussion questions

- What did only a person find?
- What would happen if this code went to production?
