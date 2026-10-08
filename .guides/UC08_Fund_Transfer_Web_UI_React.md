# UC-08 — Fund Transfer web UI with React

**Day 4 · Module: Web UI with React · Slot: 2 hrs · Demo: 25 min**

## Goal

Build a small React front-end for the Fund Transfer API so a customer can transfer money in a browser. Show that the **same Copilot practices work in a different stack (JavaScript)**, and review the things that matter in web code: **CORS, client-side vs server-side validation, secrets in the browser, XSS**.

## Time plan (120 min)

| Time        | Activity                                                                             |
| ----------- | ------------------------------------------------------------------------------------ |
| 0–45 min    | Concepts (browser vs server code, React basics, fetch calls, CORS, validation, XSS)  |
| 45–70 min   | Demo (25 min)                                                                        |
| 70–110 min  | Hands-on                                                                             |
| 110–120 min | Discussion                                                                           |

## Before the session

- Fund Transfer REST API from UC-07 running locally (`uvicorn app.main:app --reload`).
- Node.js 20+ and npm installed, VS Code with Copilot.
- Rehearse the scaffold once (`npm create vite@latest simple-bank-web -- --template react`) so the live demo is quick.
- Save the finished UI in a branch like `uc08-done`.

---

## Demo

### Step 1 — The browser app is separate from the API (4 min)

```bash
npm create vite@latest simple-bank-web -- --template react
cd simple-bank-web
npm install
npm run dev
```

Open http://localhost:5173. Point out: **two servers** — Vite serves the UI on port 5173, FastAPI serves the API on port 8000. The browser talks to both.

### Step 2 — CORS: the first web-specific problem (5 min)

With the API project open, in Copilot Chat (Agent mode):

```text
The React app at http://localhost:5173 calls this FastAPI app at http://localhost:8000.
The browser blocks the call with a CORS error. Add CORSMiddleware that allows only
http://localhost:5173. Do not use allow_origins=["*"].
```

Show the failure in **DevTools → Console**, then the fix.

Note to Trainees: _"The browser blocks cross-origin calls by default — a person decides which origins are allowed."_

### Step 3 — Repository instructions, then the transfer form (8 min)

Create `.github/copilot-instructions.md` in the web app:

```markdown
# Simple Bank web app - Copilot instructions

- React with Vite and functional components.
- Call the API only under /api/v1; read the base URL from import.meta.env.VITE_API_BASE.
- Never put secrets or API keys in browser code — it is public.
- Show API error codes as friendly text; never render raw HTML.
```

Then:

```text
Using the Fund Transfer API (POST /api/v1/transfers; error codes INSUFFICIENT_BALANCE,
DAILY_LIMIT_EXCEEDED, SAME_ACCOUNT, ACCOUNT_INACTIVE, INVALID_AMOUNT), create a React
component TransferForm with fields from_account, to_account, amount. On submit, POST JSON
to /api/v1/transfers using fetch. On success show the transaction ID; on failure show the
error code with a friendly message. Disable the button while the request is going.
```

Review with the class:

- Is `amount` sent exactly as typed?
- Is every error code from the spec handled?
- Any secret in the React code? (Browser code is **public**.)

### Step 4 — Validate in the browser and on the server (4 min)

Ask Copilot to add a client-side check (amount > 0, both accounts filled). Then temporarily remove the server-side check in the API and show with `curl` that a bad amount still gets through. Put the check back.

Note to Trainees: _"Browser validation is for the user; server validation is for safety."_

### Step 5 — Review like a web developer (4 min)

- **DevTools → Network**: inspect the POST request and the response.
- **XSS**: React escapes text by default; `dangerouslySetInnerHTML` is a red flag.
- **Masked data**: the API returns masked account numbers (from UC-04); the UI must never show full numbers.

Run a Copilot review:

```text
Review the TransferForm component as a bank security reviewer. Check for secrets,
XSS risks, and missing error handling. Show a table: Problem | Severity | Fix.
```

---

## Common mistakes (show at the end)

| Mistake                | Example today                        | Fix                           |
| ---------------------- | ------------------------------------ | ----------------------------- |
| Allow all origins      | `allow_origins=["*"]`                | Allow only the web app origin |
| Secrets in the browser | An API key inside React code         | Keys stay on the server       |
| Trusting the browser   | Only the form checks amount > 0      | Validate again in the API     |
| Rendering raw HTML     | `dangerouslySetInnerHTML` for errors | Render error text as text     |

## Hands-on (40 min)

1. Add a success panel and an error panel with friendly messages for every error code in the spec.
2. Disable **Transfer** until both accounts are filled and the amount is a positive number; add a Reset button.
3. Run `npm run build` — the `dist/` folder holds static files that can be hosted on any web server or S3/CloudFront.
4. Optional: write one Vitest test — the button is disabled when the amount is empty.
5. Swap screens with another team and check the mistakes table together.

## Discussion questions

- What was different between prompting Copilot for Python and for React?
- Which checks must stay on the server even if the UI already does them?
