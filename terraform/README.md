# portal-backend Terraform

ECS Fargate service for portal-backend behind the shared ALB (`af-load-balancer`). Staging and prod are the same code with their own state and `envs/*.tfvars`. Layout and conventions follow db-service's `terraform/`.

## Layout

- `main.tf`, `backend.tf`, `variables.tf`, `outputs.tf`: provider, S3 backend (key given at init), inputs.
- `ecr.tf`, `ecs.tf`, `alb.tf`, `security.tf`, `iam.tf`, `logs.tf`: the AWS resources. The ALB, VPC and wildcard cert already exist; we only add a target group and a listener rule.
- `envs/staging.tfvars`, `envs/prod.tfvars`: non-secret values (hostname, listener priority, capacity).
- `dns/`: a separate root that owns the Cloudflare CNAME for the hostname. Kept apart because pointing the name at the ALB is the cutover step.

## Secrets

Passed as `TF_VAR_<name>` environment variables, never committed. GitHub secrets can't be read back, so take each value from the Lambda for that environment (`PortalBackendStaging` / `PortalBackendProd`), where it is the env var of the same name. Use the same `JWT_SECRET_KEY` as Lambda so tokens stay valid if traffic moves back.

| Variable | GitHub secret (where it is stored) |
|---|---|
| `jwt_secret_key` | `JWT_SECRET_KEY` (environment) |
| `db_service_url` | `DB_SERVICE_URL` (environment) |
| `db_service_token` | `DB_SERVICE_TOKEN` (environment) |
| `otp_service_url` | `OTP_SERVICE_URL` (environment) |
| `sashakt_api_url` | `SASHAKT_API_URL` (environment) |
| `sashakt_webapp_url` | `SASHAKT_WEBAPP_URL` (environment) |
| `sashakt_admin_email` | `SASHAKT_ADMIN_EMAIL` (environment) |
| `sashakt_admin_password` | `SASHAKT_ADMIN_PASSWORD` (environment) |
| `sqs_access_key` | `SQS_ACCESS_KEY` (repository) |
| `sqs_secret_access_key` | `SQS_SECRET_ACCESS_KEY` (repository) |
| `aws_sqs_url` | `AWS_SQS_URL` (repository) |

## Apply

```sh
cd terraform
terraform init -reconfigure -backend-config="key=portal-backend/staging/terraform.tfstate"
terraform plan  -var-file=envs/staging.tfvars
terraform apply -var-file=envs/staging.tfvars
```

For prod use `portal-backend/prod/terraform.tfstate` and `envs/prod.tfvars`.

## First-time order

1. Apply with the capacity in the tfvars (staging ships at `min_capacity = 0`, `desired_count = 0`). No tasks start, so nothing fails on a missing image.
2. Run the "Deploy to ECS (staging)" workflow to build and push the first image.
3. Raise `min_capacity` and `desired_count` in the tfvars in a reviewed change and apply.

## Changing a secret takes two steps

`terraform apply` registers a new task definition revision, but the service ignores `task_definition`, so the new value is not live yet. It goes live on the next run of the deploy workflow, which copies the latest revision.

## DNS

```sh
cd terraform/dns
terraform init -reconfigure -backend-config="key=portal-backend/dns-staging/terraform.tfstate"
export TF_VAR_cloudflare_api_token=...   # scoped token: Zone > DNS > Edit
terraform apply -var cloudflare_zone_id=<zone id> -var name=staging-portal-backend
```

By default the record points at the ALB. To put the same name on API Gateway first (step 1 of `docs/move-to-ecs.md`), add `-var target=<api gateway domain>`; cutover is applying again without `target`. Prod uses `dns-prod` as the state key and `-var name=portal-backend`.
