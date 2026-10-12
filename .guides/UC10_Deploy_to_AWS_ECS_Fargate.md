# UC-10 — Deploy the Fund Transfer API to AWS (ECS Fargate)

**Day 5 · Module: Cloud-Native Build & CI/CD · Slot: 2 hrs · Demo: 30 min**

## Goal

Take the Fund Transfer API in `backend/` to the cloud. Add a health check and simple logs, write a Dockerfile, and ask Copilot to create a GitHub Actions pipeline:

**build → test → scan → push image to ECR → deploy to ECS Fargate → smoke test**

Copilot also uses the AWS CLI to show what is already set up in AWS. **AWS setup is done before the session.**

## Time plan (120 min)

| Time        | Activity                                                                          |
| ----------- | --------------------------------------------------------------------------------- |
| 0–40 min    | Concepts (REST APIs, health checks, logging, testing, Docker, CI/CD, ECS, GitOps) |
| 40–70 min   | Demo (30 min)                                                                     |
| 70–110 min  | Hands-on                                                                          |
| 110–120 min | Discussion                                                                        |

## Names used in this runbook

| Item                        | Value                                                |
| --------------------------- | ---------------------------------------------------- |
| AWS region                  | `eu-north-1` (Europe – Stockholm)                    |
| AWS CLI profile             | `itc`                                                |
| ECR repository              | `itc/fast-api-demo` (format `<namespace>/<image-name>`) |
| ECS cluster / service       | `simple-bank` / `fund-transfer-svc`                  |
| Task definition / container | `fund-transfer-task` / `fund-transfer`               |
| Container port              | `8000`                                               |
| GitHub secret / variable    | `AWS_ROLE_ARN` / `APP_URL`                           |

If you pick other names, change them in the prompts too.

## Before the session (do NOT set up AWS live)

### 1. Rehearse the code

On a branch `uc10-done`, do Demo Steps 2–4 (health check, logs, Dockerfile). ECS needs an image that already has `/health`, so the first image you push comes from this branch.

### 2. AWS console — region and ECR

1. Sign in to the AWS console as a user who can manage ECR, ECS, load balancers (EC2), IAM and CloudWatch Logs.
2. Set the region (top right) to **Europe (Stockholm) `eu-north-1`**.
3. **ECR → Create repository** → Private → enter `<namespace>/<image-name>`, e.g. `itc/fast-api-demo`.

### 3. AWS CLI on the trainer laptop

Install AWS CLI v2 (Windows or Mac). You can ask Copilot Chat (Agent mode):

```text
Install AWS CLI
```

Then run these **yourself** in a terminal — never type keys into Copilot Chat:

```bash
aws configure list             # everything is <not set> — no credentials yet
aws configure --profile itc    # access key ID, secret access key, region eu-north-1, output format: press Enter
aws configure list-profiles    # if you see "itc", you are all set
```

The keys are saved in `~/.aws/credentials` on your laptop. Never paste them into chat, a prompt, or a file in the repo.

### 4. Push a first image to ECR

Open the repository in ECR → **View push commands**, or run from the `uc10-done` branch:

```bash
aws ecr get-login-password --region eu-north-1 --profile itc | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-north-1.amazonaws.com
docker build --platform linux/amd64 -t <account-id>.dkr.ecr.eu-north-1.amazonaws.com/itc/fast-api-demo:bootstrap backend
docker push <account-id>.dkr.ecr.eu-north-1.amazonaws.com/itc/fast-api-demo:bootstrap
```

`--platform linux/amd64` matters on Apple Silicon Macs: the Fargate task runs on Linux/X86_64.

### 5. AWS console — ECS Fargate

**ECS → Task definitions → Create new task definition**

- Family `fund-transfer-task`, launch type **AWS Fargate**, OS/architecture **Linux/X86_64**, 0.5 vCPU, 1 GB memory.
- Task execution role: **Create new role** (lets ECS pull the image and write logs).
- Container `fund-transfer` → Image URI: click **Browse ECR images** → pick `itc/fast-api-demo` and tag `bootstrap`. This fills in the image URI for you.
- Port mapping: container port `8000`, TCP, HTTP.
- Log collection: on (Amazon CloudWatch). Whatever the app prints to stdout ends up here.

**ECS → Clusters → Create cluster** → name `simple-bank`, infrastructure **AWS Fargate (serverless)**.

**Cluster `simple-bank` → Services → Create**

- Launch type FARGATE, task definition `fund-transfer-task` (latest), service name `fund-transfer-svc`, 1 desired task.
- Networking: default VPC, public subnets, **Public IP on**. Security group: inbound TCP `80` (load balancer) and `8000` (load balancer → task). _Demo only — in production allow `8000` only from the load balancer._
- Load balancing: **Application Load Balancer** → create `fund-transfer-alb`, listener HTTP `80`, new target group `fund-transfer-tg` with health check path **`/health`**.
- When the service is stable, copy the load balancer **DNS name**. This is your `APP_URL`, e.g. `http://fund-transfer-alb-123456.eu-north-1.elb.amazonaws.com`.

> **Database:** transfers need PostgreSQL (`DATABASE_URL`). This demo deploys without a database. `/health` works, and `POST /api/v1/transfers` returns `401 UNAUTHENTICATED` because the standalone app has no bank sign-in. Connecting RDS is out of scope.

### 6. GitHub ↔ AWS (no keys in the pipeline)

1. **IAM → Identity providers → Add provider** → OpenID Connect, URL `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
2. **IAM → Roles → Create role** → Web identity → that provider, your GitHub organisation, repository `simple-bank`. Give it only what the pipeline needs: push to `itc/fast-api-demo` (plus `ecr:GetAuthorizationToken`), `ecs:RegisterTaskDefinition`, `ecs:DescribeTaskDefinition`, `ecs:UpdateService` and `ecs:DescribeServices` on `fund-transfer-svc`, and `iam:PassRole` on the task execution role.
3. GitHub repo → **Settings → Secrets and variables → Actions**: secret `AWS_ROLE_ARN` (the role ARN), variable `APP_URL` (the load balancer URL).
4. GitHub repo → **Settings → Environments** → new environment `production` → add yourself as a required reviewer.

> Can't use OIDC in your account? Store a deploy-only user's keys as repo secrets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` and change the Step 5 prompt to match. Never put keys in the workflow file.

### 7. Last checks

- Save the task definition on `main`, then commit and push it:
  ```bash
  mkdir -p .aws
  aws ecs describe-task-definition --task-definition fund-transfer-task --query taskDefinition --profile itc > .aws/task-definition.json
  ```
- `curl <APP_URL>/health` returns `{"status":"UP"}`.
- Run the full pipeline once from `uc10-done` (temporarily add the branch to `on: push: branches`). Note how long it takes (usually 6–10 min, plus the approval).
- Save the finished code in `uc10-done`. If the live demo goes wrong, switch to it and carry on.

---

## Demo

### Step 1 — Let Copilot see AWS (4 min)

In the VS Code terminal, show that the profile is ready. Do **not** type keys while sharing your screen.

```bash
aws configure list-profiles
```

Copilot Chat (Agent mode):

```text
Run export AWS_PROFILE=itc in the terminal (PowerShell: $env:AWS_PROFILE="itc").
Then, using read-only AWS CLI commands only, get the resources available in this profile in eu-north-1:
the caller identity, ECR repositories and their image tags, ECS clusters, services and running tasks,
and the load balancer DNS name. Show the result as a short table.
```

Allow each command as Copilot asks. Point out:

- Copilot uses the CLI profile — the keys never appear in chat.
- Read every command before you click **Allow**. `list` and `describe` are safe; `delete` and `update` are not.
- The `bootstrap` image is running now. The pipeline will replace it.

### Step 2 — Health check and simple logs (6 min)

```text
In the FastAPI app in #file:backend/src/simple_bank/main.py :
1. Add GET /health that returns {"status": "UP"}. It must not use the database, so it works even when DATABASE_URL is not set.
2. Set up simple logging at startup: INFO level, one line per event, printed to stdout. Include the extra fields
   that #file:backend/src/simple_bank/logging.py already adds. Account numbers must stay masked (XXXX1234).
3. Log one line per HTTP request: method, path, status code and time taken. Skip /health so health checks don't flood the logs.
4. Add contract tests in backend/tests/contract for /health and the request log line.
Do not change the transfer rules.
```

Point out:

- The load balancer calls `/health` every 30 seconds. If it fails, ECS replaces the task.
- Logs go to stdout → CloudWatch picks them up. No log files in the container.
- Masked account numbers only — many people can read logs.

### Step 3 — Run it and test it (3 min)

```bash
cd backend
uv run pytest tests/unit tests/contract
uv run uvicorn simple_bank.main:app --reload
```

In a second terminal (Windows: use Git Bash):

```bash
curl http://localhost:8000/health
curl -i -X POST http://localhost:8000/api/v1/transfers -H "Content-Type: application/json" -d '{"from_account":"12345678","to_account":"87654321","amount":"10.00"}'
```

Expect `{"status":"UP"}`, then `401` with `UNAUTHENTICATED`. Show the request log line in the uvicorn terminal.

Point out: the PostgreSQL integration tests are skipped here (no `TEST_DATABASE_URL`). The pipeline will run them against a Postgres container.

### Step 4 — Dockerfile (5 min)

```text
Create backend/Dockerfile and backend/.dockerignore for the FastAPI app in backend/
(package simple_bank in src/, dependencies managed with uv and uv.lock):
- Stage 1: install the app and its dependencies with uv from uv.lock, without dev dependencies.
- Stage 2: python:3.12-slim, copy in the virtual environment, run as a non-root user, expose port 8000,
  and start with: uvicorn simple_bank.main:app --host 0.0.0.0 --port 8000
- Keep .venv, tests and any .env file out of the image.
Add short comments explaining each part.
```

Build and run:

```bash
cd backend
docker build --platform linux/amd64 -t fund-transfer .
docker run --rm -p 8000:8000 fund-transfer
curl http://localhost:8000/health
```

Point out: two stages = smaller image; non-root = safer; `.dockerignore` keeps `.env` files off the image.

### Step 5 — GitHub Actions pipeline (8 min)

```text
Create .github/workflows/deploy.yml that runs on push to main (and can be started by hand). In order:
1. Build and test: in backend/, set up Python 3.12 and uv, run uv sync --frozen, then
   uv run pytest -m "not performance" with a postgres:16 service container
   (database simple_bank_test, POSTGRES_HOST_AUTH_METHOD=trust) and TEST_DATABASE_URL pointing to it.
2. Scan: build the Docker image from backend/ and scan it with Trivy.
   Fail on HIGH or CRITICAL vulnerabilities that have a fix.
3. Push: only if the scan passes. Log in to AWS with OIDC (role from secret AWS_ROLE_ARN, region eu-north-1),
   log in to ECR, and push to repository itc/fast-api-demo tagged with the commit SHA.
4. Deploy: use the GitHub environment "production" so a person must approve.
   Put the new image into .aws/task-definition.json (container fund-transfer) and deploy it to
   service fund-transfer-svc in cluster simple-bank. Wait until the service is stable.
5. Smoke test: call vars.APP_URL/health with a few retries. Fail unless it returns {"status": "UP"}.
No AWS keys in the file.
```

Review the file with the class:

- No AWS keys — OIDC with `permissions: id-token: write`
- Image tag is the commit SHA, not `latest`
- Scan runs before push; a failed scan stops the push
- Deploy waits for approval and for the service to be stable
- Smoke test calls `/health` on the load balancer URL

Push it:

```bash
git add -A
git commit -m "Add health check, Dockerfile and deploy pipeline"
git push
```

### Step 6 — Watch it run (4 min)

- Open the **Actions** tab.
- While it runs, explain **GitOps** in one line: _instead of the pipeline pushing to the cloud, a tool in the cluster pulls the latest approved version from Git._
- Approve the **production** deploy when it asks.
- Check the smoke test passes.

Back in Copilot Chat:

```text
Using AWS_PROFILE=itc, show which image tag the fund-transfer-svc service is running now,
and the last 20 lines from its CloudWatch log group.
```

Point out: the tag is the commit SHA you just pushed, and the logs show request lines with masked accounts only.

> If it fails or is slow, show the successful run from your rehearsal.

---

## If something goes wrong

| Problem                                                   | Likely cause                                         | Fix                                                                    |
| --------------------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------- |
| Task stops with `exec format error`                       | Image built for ARM on an Apple Silicon Mac          | Build with `--platform linux/amd64`                                    |
| Target group unhealthy, tasks keep restarting             | Health check path is not `/health`, or port 8000 blocked | Set the health check path to `/health`; allow 8000 from the load balancer |
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | Role trust doesn't match the repo, or no `id-token: write` | Check the role's GitHub org/repo and the workflow `permissions`        |
| Deploy fails with `iam:PassRole`                          | Role can't hand the execution role to ECS            | Add `iam:PassRole` on the task execution role                          |
| Trivy fails the build                                     | Old packages in the image                            | Rebuild on the latest `python:3.12-slim`; discuss the report           |
| `git push` refused for the workflow file                  | Your GitHub token lacks the `workflow` scope         | `gh auth refresh -s workflow`, then push again                         |
| Copilot's AWS commands fail or hit the wrong account      | `AWS_PROFILE` not set in Copilot's terminal          | Set it again; check with `aws sts get-caller-identity`                 |

## Hands-on (40 min)

On your own service:

1. Install the AWS CLI (or ask Copilot: `Install AWS CLI`). In your **own** terminal, run `aws configure --profile itc` with the keys the trainer gives your team, then `aws configure list-profiles`.
2. Ask Copilot to get the resources available in your profile — read-only commands only.
3. Add a health check and simple logs. Run `uv run pytest tests/unit tests/contract`.
4. Write a Dockerfile, build it and run it locally.
5. Ask Copilot to create the pipeline up to "push image to ECR". (Deploy only if the trainer has set up an ECS service for your team.)
6. Swap pipelines with another team and check: no keys in the file, SHA tag, scan before push, approval before deploy.

## Discussion questions

- What did the Trivy scan find? Which findings had a fix?
- Did Copilot's first pipeline have any mistakes (like `latest`, AWS keys, or a missing `id-token: write`)?
- Which AWS commands would you never let Copilot run without reading them first?

## After the course

- Set the service to 0 tasks and delete the load balancer — both cost money even when idle:
  ```bash
  aws ecs update-service --cluster simple-bank --service fund-transfer-svc --desired-count 0 --profile itc
  ```
- Deactivate the access keys that were handed out for the `itc` profiles.
