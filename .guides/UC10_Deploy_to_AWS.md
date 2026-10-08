# UC-10 — Deploy the Fund Transfer API to AWS

**Day 5 · Module: Cloud-Native Build & CI/CD · Slot: 2 hrs · Demo: 30 min**

## Goal
Take the Fund Transfer API from UC-06/07 and make it ready for the cloud: health check, logs, tests, Docker image, and a GitHub Actions pipeline that deploys to **AWS ECS Fargate**.

## Time plan (120 min)
| Time | Activity |
|---|---|
| 0–40 min | Concepts (REST APIs, health checks, logging, testing, Docker, CI/CD, ECS, GitOps) |
| 40–70 min | Demo (30 min) |
| 70–110 min | Hands-on |
| 110–120 min | Discussion |

## Before the session (do NOT set up AWS live)
In AWS (region `ap-south-1`, Mumbai):
- ECR repository: `simple-bank/fund-transfer`
- ECS cluster `simple-bank` with a Fargate service `fund-transfer-svc` behind a load balancer
- An IAM role that GitHub Actions can use (OIDC)

In GitHub repo settings:
- Secret `AWS_ROLE_ARN`
- Variable `APP_URL` (the load balancer URL)

Save the ECS task definition as `.aws/task-definition.json`.
Run the full pipeline once and note how long it takes (usually 6–10 min).

---

## Demo

### Step 1 — Health check and logs (6 min)
Copilot Chat (Agent mode):
```text
In the FastAPI Fund Transfer app:
1. Add a health endpoint at /health that returns {"status": "UP"}.
2. Add simple logging for each transfer: transaction ID, status, and masked account numbers only (XXXX1234).
3. Move settings like the daily limit to .env with pydantic-settings so they can be changed without code changes.
```
Run the app and test:
```bash
uvicorn app.main:app --reload
curl http://localhost:8000/health
```
Point out: the health check tells AWS if the app is working.

### Step 2 — Integration test (4 min)
```text
Add an integration test using FastAPI's TestClient for POST /api/v1/transfers:
one successful transfer and one that fails with INSUFFICIENT_BALANCE.
```
Run `uv run pytest`.

### Step 3 — Dockerfile (6 min)
```text
Create a multi-stage Dockerfile for this FastAPI app:
Stage 1 builds the app and its dependencies with uv.
Stage 2 uses a small python:3.12-slim runtime image, runs as a non-root user, and exposes port 8000.
Add a .dockerignore file. Add short comments explaining each part.
```
Build and run:
```bash
docker build -t fund-transfer .
docker run -p 8000:8000 fund-transfer
```
Point out: two stages = smaller image; non-root = safer.

### Step 4 — GitHub Actions pipeline (8 min)
```text
Create .github/workflows/deploy.yml that runs on push to main:
1. Install dependencies with uv and run tests with pytest (Python 3.12).
2. Build the Docker image and scan it with Trivy. Fail if HIGH or CRITICAL issues are found.
3. Log in to AWS using OIDC (role from secret AWS_ROLE_ARN, region ap-south-1),
   log in to ECR and push the image tagged with the commit SHA.
4. Deploy to ECS service fund-transfer-svc in cluster simple-bank using .aws/task-definition.json.
   Use a GitHub environment called "production" so a person must approve the deploy.
5. Smoke test: call vars.APP_URL/health and expect status UP.
```
Review the file with the class:
- No AWS keys in the file (OIDC is used)
- Image tag is the commit SHA, not `latest`
- Scan happens before push
- Deploy waits for approval

Push it:
```bash
git add -A
git commit -m "Add Docker and deploy pipeline"
git push
```

### Step 5 — Watch it run (6 min)
- Open the **Actions** tab.
- While it runs, explain **GitOps** in one line: *instead of the pipeline pushing to the cloud, a tool in the cluster pulls the latest approved version from Git.*
- Approve the **production** deploy when it asks.
- Check the smoke test passes.

> If it fails or is slow, show the successful run from your rehearsal.

---

## Hands-on (40 min)
On your own service:
1. Add a health check and masked logging.
2. Write a Dockerfile, build it and run it locally.
3. Ask Copilot to create the pipeline up to "push image to ECR". (Deploy only if the trainer has set up an ECS service for your team.)
4. Swap pipelines with another team and check: no keys in the file, scan before push, approval before deploy.

## Discussion questions
- What did the Trivy scan find?
- Did Copilot's first pipeline have any mistakes (like using `latest` or AWS keys)?
