# UC-09 — Old Savings Interest Calculator app: assess and decide

**Day 5 · Module: Modernization — Assessment & Decision · Slot: 2 hrs · Demo: 25 min**

## Goal

Use Copilot to understand a small old app, list its problems, pick one of the **6 Rs** for each part, and write a modernization spec. That spec is used in Case Study 1 (UC-12).

## Time plan (120 min)

| Time        | Activity                                                                                 |
| ----------- | ---------------------------------------------------------------------------------------- |
| 0–45 min    | Concepts (old vs modern apps, why modernize, assessment, the 6 Rs, AI for code analysis) |
| 45–70 min   | Demo (25 min)                                                                            |
| 70–110 min  | Hands-on                                                                                 |
| 110–120 min | Discussion                                                                               |

### The 6 Rs (quick reminder)

| R          | Meaning                              |
| ---------- | ------------------------------------ |
| Rehost     | Move as-is to the cloud              |
| Replatform | Small changes, e.g. managed database |
| Refactor   | Rewrite / restructure the code       |
| Repurchase | Replace with a ready-made product    |
| Retire     | Switch it off                        |
| Retain     | Keep it as it is for now             |

## Before the session

Create a folder `legacy-interest-app/` with these files. The problems are **on purpose**.

**`db_helper.py`**

```python
import pymysql

class DbHelper:
    @staticmethod
    def get_connection():
        return pymysql.connect(
            host="10.0.0.5", port=3306, user="admin",
            password="admin123", database="bank", autocommit=True)
```

**`interest_job.py`** — runs every night

```python
from db_helper import DbHelper
from savings_interest import SavingsInterest

def main():
    con = DbHelper.get_connection()
    cur = con.cursor()
    cur.execute("SELECT acc_no, balance, acc_type FROM savings")
    for acc_no, balance, acc_type in cur.fetchall():
        interest = SavingsInterest().calc(balance, acc_type)
        cur.execute(
            "UPDATE savings SET balance = balance + " + str(interest)
            + " WHERE acc_no = '" + acc_no + "'")
        print("Interest " + str(interest) + " added to account " + acc_no)

if __name__ == "__main__":
    main()
```

**`savings_interest.py`** — same as in UC-07

```python
class SavingsInterest:
    def calc(self, bal, acc_type):
        r = 0
        if acc_type.upper() == "S":
            r = 3.5
        elif acc_type.upper() == "SC":
            r = 4.0
        elif acc_type.upper() == "STAFF":
            r = 4.5
        i = bal * r / 100 / 12
        if bal < 1000:
            i = 0
        return round(i, 2)
```

**`interest_report.py`** — prints a monthly report file

```python
from db_helper import DbHelper

def main():
    con = DbHelper.get_connection()
    cur = con.cursor()
    cur.execute("SELECT acc_no, balance FROM savings")
    with open("C:/reports/interest.txt", "w") as f:
        for acc_no, balance in cur.fetchall():
            f.write(acc_no + "," + str(balance) + "\n")

if __name__ == "__main__":
    main()
```

Tell the class: _"The bank now has a reporting tool (dashboard) that can produce this report."_

---

## Demo

### Step 1 — Explain the app (5 min)

Copilot Chat (Ask mode):

```text
Look at the files in #folder:legacy-interest-app . Explain in simple words:
1. What does this app do?
2. What does each file do?
3. Which database tables does it use?
4. What business rules are in the code?
```

### Step 2 — Draw the dependencies (4 min)

```text
Draw a simple Mermaid diagram showing how the files in legacy-interest-app
connect to each other and to the database.
```

Open it in Markdown preview.

### Step 3 — List the problems (6 min)

```text
List the problems in legacy-interest-app as a table:
Problem | File | Why it matters for a bank | Severity (High/Medium/Low).
```

Expected problems:
| Problem | Why it matters |
|---|---|
| Hard-coded database password | Anyone with the code gets database access |
| SQL built by joining strings | SQL injection risk |
| `float` for money | Small rounding errors in customer balances |
| Full account number printed | Sensitive data in logs |
| No transaction; if the job fails midway and runs again, some accounts get interest twice | Wrong balances |
| Crashes if account type is missing | Job stops for all customers |

### Step 4 — Pick the 6 Rs (5 min)

```text
For each part of legacy-interest-app — (a) interest calculation, (b) nightly interest job,
(c) interest report, (d) database helper — suggest one of the 6 Rs
(Rehost, Replatform, Refactor, Repurchase, Retire, Retain) with a short reason.
Note: the bank already has a reporting tool that can create the interest report.
```

Discuss. A good answer:
| Part | R | Why |
|---|---|---|
| Interest calculation | Refactor | Core logic; needs correct money handling and tests |
| Nightly interest job | Refactor | Must be safe to re-run |
| Interest report | Retire | Reporting tool already does it |
| Database helper | Retire | Replace with proper config and a connection pool |

Note to Trainees: _"AI suggests; the team decides and writes down why."_

### Step 5 — Write the modernization spec (5 min)

```text
/speckit.specify Modernize the savings interest calculation from legacy-interest-app into a
REST service: POST /api/v1/interest/calculate with balance and account type, returns monthly interest.
It must give the SAME results as the old SavingsInterest.calc for the same inputs, except:
use Decimal (round HALF_UP to 2 decimals) and return an error for an unknown or empty account type.
Include examples comparing old and new results.
```

---

## Hands-on (40 min)

Using the same old app:

1. Use Copilot to explain it and list problems. **Check 2 of Copilot's claims by reading the code yourself.**
2. Pick an R for each part and write one line explaining why.
3. Write your modernization spec with `/speckit.specify`.

## Discussion questions

- Did Copilot say anything wrong about the code?
- Did any team choose a different R? Why?
