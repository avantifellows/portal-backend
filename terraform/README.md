# portal-backend Terraform

ECS Fargate service for portal-backend behind the shared ALB (`af-load-balancer`). Staging and prod are the same code with their own state and `envs/*.tfvars`. Layout and conventions follow db-service's `terraform/`.

## Layout

- `main.tf`, `backend.tf`, `variables.tf`, `outputs.tf`: provider, S3 backend (key given at init), inputs.
- `ecr.tf`, `ecs.tf`, `alb.tf`, `security.tf`, `iam.tf`, `logs.tf`, `secrets.tf`: the AWS resources. The ALB, VPC and wildcard cert already exist; we only add a target group and a listener rule.
- `envs/staging.tfvars`, `envs/prod.tfvars`: non-secret values (hostname, listener priority, capacity).
- `dns/`: a separate root that owns the Cloudflare CNAME for the hostname. Kept apart because pointing the name at the ALB is the cutover step.

## Secrets

All app values are in one Secrets Manager secret per environment, `portal-backend/<env>/app`. It's a JSON object with one key per env var, and the container gets them as normal env vars (`secrets` in `ecs.tf`). Terraform creates only the empty secret, so the values never appear in state, plans or the task definition. Only `WEB_CONCURRENCY` and `AWS_DEFAULT_REGION` are plain `environment` entries.

Keys (the list is `local.secret_keys` in `secrets.tf`): `JWT_SECRET_KEY`, `DB_SERVICE_URL`, `DB_SERVICE_TOKEN`, `SQS_ACCESS_KEY`, `SQS_SECRET_ACCESS_KEY`, `AWS_SQS_URL`, `OTP_SERVICE_URL`, `SASHAKT_API_URL`, `SASHAKT_WEBAPP_URL`, `SASHAKT_ADMIN_EMAIL`, `SASHAKT_ADMIN_PASSWORD`.

The Lambda still gets the same values from GitHub secrets (environment `Staging` / `Production`; the SQS ones are repo-level). GitHub secrets can't be read back, so fill the secret from the Lambda for that environment. That also keeps `JWT_SECRET_KEY` the same, so tokens stay valid on both.

```sh
umask 077
aws lambda get-function-configuration --function-name PortalBackendStaging \
  --query 'Environment.Variables.{JWT_SECRET_KEY:JWT_SECRET_KEY,DB_SERVICE_URL:DB_SERVICE_URL,DB_SERVICE_TOKEN:DB_SERVICE_TOKEN,SQS_ACCESS_KEY:SQS_ACCESS_KEY,SQS_SECRET_ACCESS_KEY:SQS_SECRET_ACCESS_KEY,AWS_SQS_URL:AWS_SQS_URL,OTP_SERVICE_URL:OTP_SERVICE_URL,SASHAKT_API_URL:SASHAKT_API_URL,SASHAKT_WEBAPP_URL:SASHAKT_WEBAPP_URL,SASHAKT_ADMIN_EMAIL:SASHAKT_ADMIN_EMAIL,SASHAKT_ADMIN_PASSWORD:SASHAKT_ADMIN_PASSWORD}' \
  > app.json
jq -e 'length == 11 and all(.[]; type == "string" and length > 0)' app.json > /dev/null   # every key present and non-empty
aws secretsmanager put-secret-value --secret-id portal-backend/staging/app --secret-string file://app.json
rm app.json
```

For prod use `PortalBackendProd` and `portal-backend/prod/app`.

## Apply

```sh
cd terraform
terraform init -reconfigure -backend-config="key=portal-backend/staging/terraform.tfstate"
terraform plan  -var-file=envs/staging.tfvars
terraform apply -var-file=envs/staging.tfvars
```

For prod use `portal-backend/prod/terraform.tfstate` and `envs/prod.tfvars`.

## First-time order

The service defaults are `desired_count = 2` / `min_capacity = 2` (neither tfvars file overrides them). For a new environment, set both to `0` in its tfvars for the first apply, so no task starts before there is an image and a filled secret.

1. Apply. This creates the empty secret, among everything else.
2. Fill the secret (see "Secrets"). Tasks can't start until it has every key.
3. Run the deploy workflow to build and push the first image.
4. Raise `min_capacity` and `desired_count` in the tfvars in a reviewed change and apply.

## Changing a value or the container

**A secret value:** `put-secret-value` with the full JSON (see "Secrets"), then force a new deployment so every task picks it up:

```sh
aws ecs update-service --cluster portal-backend-staging --service portal-backend-staging --force-new-deployment
```

Tasks read the secret when they start. So until the redeploy, tasks started by autoscaling get the new value and older ones keep the old one. Change the matching GitHub secret too, or the Lambda and ECS drift apart.

**Anything else in the container** (cpu, memory, plain env, health check, a new secret key): change `ecs.tf`/`secrets.tf` and apply. The deploy workflow reads the task definition from this Terraform state, so the change goes live on the next deploy. Merge to `main` and apply from `main`; an apply from an older branch would put the old definition back.

## How the deploy workflow reads the task definition

`deploy_ecs_staging.yml` has no `ecs:DescribeTaskDefinition`, because that permission can't be limited to one family and would expose every task definition in the account. Instead it reads `aws_ecs_task_definition.this` and the `alb_dns_name` output from `s3://111766607077-dbservice-test-terraform-state/portal-backend/staging/terraform.tfstate`, swaps in the new image, registers it and updates the service. It fails without printing anything if the state has plain-text env vars other than the two above, or secrets outside `portal-backend/staging/app`.

It runs as the IAM role `portal-backend-ecs-staging-deploy` via GitHub OIDC (environment `Staging`). That role can read only that state file (the current version), push to and pull from this ECR repo, register this family, update this service, and pass the execution role. ECR tags are immutable, so a re-run of the same commit reuses its image.

## DNS

```sh
cd terraform/dns
terraform init -reconfigure -backend-config="key=portal-backend/dns-staging/terraform.tfstate"
export TF_VAR_cloudflare_api_token=...   # scoped token: Zone > DNS > Edit
terraform apply -var cloudflare_zone_id=<zone id> -var name=staging-portal-backend
```

By default the record points at the ALB. To put the same name on API Gateway first (step 1 of `docs/move-to-ecs.md`), add `-var target=<api gateway domain>`; cutover is applying again without `target`. Prod uses `dns-prod` as the state key and `-var name=portal-backend`.
