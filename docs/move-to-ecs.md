# Move portal-backend from Lambda to ECS

Owner: Abhinav

## Why

portal-backend runs on Lambda behind API Gateway. Every request gets its own Lambda instance, and each instance opens fresh HTTPS connections to db-service. Nothing is shared between requests: no connection pool, no in-memory cache that lasts.

On normal days this is fine. On the Punjab live test (29 Sep, 07:30–13:30 IST) it wasn't:

| | Test morning | Normal morning (1 Oct) |
|---|---|---|
| Invocations | 24 lakh | 72k |
| Peak concurrent Lambdas | 3,145 | 7 |
| Errors | 1.27 lakh | 0 |
| p50 / p95 latency | 9 ms / 29.6 s | 4 ms / 55 ms |

3,145 Lambdas at once means up to 3,145 sets of connections hitting a t3.small db-service. The p95 of 29.6 s is requests waiting until Lambda's 30 s limit kills them. Students saw this in two ways:

- **Failed logins.** The sign-in request itself timed out.
- **Getting logged out mid-test.** The access token lasts an hour, so a student who signed in at 9:30 needs a silent refresh around 10:30, right in the peak. When that refresh timed out, Gurukul (`services/validation.ts`) treated it as an invalid session and sent the student back to the portal, and the portal frontend (`token.js`, `refreshToken`) deleted the session cookies outright. The quiz page itself isn't affected: it checks its launch token once when it opens and keeps the student's identity in the tab. So "logged out" here means a student returning to Gurukul or the portal mid-test and being asked to sign in again.

33k students produced 1.6 lakh sign-ins that day, about 5 each, which fits.

The apps reading a slow backend as "not logged in" is worth fixing on its own, independent of this move: log a student out only on a real invalid-token response, not on a timeout or 5xx.

A long-running service can keep a small pool of connections to db-service and reuse them across requests, and can hold a cache. That's the main win.

## What quiz-backend already did

quiz-backend moved off Lambda for the same reason, with MongoDB instead of db-service (PR #130, Mar 2026; deploy speed-ups in #162):

- ECS Fargate on ARM64, 1 vCPU / 2 GB per task, Uvicorn with 4 workers.
- ALB in front, Cloudflare DNS pointing at it.
- Autoscaling on CPU at 50%, min 1, max 10 tasks.
- Terraform in `terraform/{testing,prod}` (~1,200 lines: ECR, ECS, ALB, IAM, security groups, autoscaling, DNS), state in S3.
- `/health` endpoint for ALB checks, Dockerfile, two deploy workflows.
- Load-tested at 5,000 concurrent users on testing before prod.

Most of this can be copied for portal-backend with names changed.

## What's different for portal-backend

1. **Connection pool to db-service.** The point of the move. One shared `requests.Session`/`httpx.Client` per worker, with timeouts. (Also in `signin-fewer-dbservice-calls.md`.)
2. **Env vars.** Today they come from GitHub secrets into the SAM template: `JWT_SECRET_KEY`, `DB_SERVICE_URL`, `DB_SERVICE_TOKEN`, `SQS_ACCESS_KEY`, `SQS_SECRET_ACCESS_KEY`, `AWS_SQS_URL`, `OTP_SERVICE_URL`, and the Sashakt ones added with the Sashakt launch (`SASHAKT_API_URL`, `SASHAKT_WEBAPP_URL`, `SASHAKT_ADMIN_EMAIL`, `SASHAKT_ADMIN_PASSWORD`). They move into the ECS task definition. Most are per-environment secrets (Staging / Production); the SQS ones are repo-level. The current list is always the `Environment.Variables` block in `templates/prod.yaml`.
3. **The URL. This is the real work.** portal-backend is reached through the raw API Gateway URL, hard-coded or configured in:
   - portal-frontend: `VITE_APP_PORTAL_BACKEND` in both deploy workflows
   - gurukul: `NEXT_PUBLIC_AF_PORTAL_BACKEND_URL`
   - quiz-frontend: `VUE_APP_PORTAL_BACKEND`
   - reporting: `PORTAL_BACKEND_URL`
   - college-predictor: default in `utils/portalSession.js`

   Give it a proper domain first (`portal-backend.avantifellows.org`, the name `terraform/dns` manages), point it at API Gateway with `-var target=<api gateway domain>`, move every consumer to the domain, and only then re-apply `terraform/dns` without `target` so it points at the ALB. That way the switch to ECS is a DNS change, not five deploys.
4. **CORS.** The allowed origins live in `app/main.py` and don't change, but check the ALB doesn't strip anything.

## Rollout

1. Custom domain on the current Lambda; move all consumers to it (staging, then prod).
2. Stand up ECS on staging from quiz-backend's Terraform. Load-test login: verify + launch-token + user-session, at a few thousand concurrent.
3. Repoint the staging domain to the ALB. Run the usual checks: EnableStudents login, AFTesting, signup, Gurukul, quiz launch, Futures.
4. Same for prod. Keep the Lambda running for a week, so rollback is just a DNS change.
