# Local access to the private Triana AWS runtime

Status: observed live on 2026-08-06. This document contains resource identity
and operating commands only; it contains no credential or environment value.

## Correct account

Use AWS CLI profile `akarsh-deepprobe`:

```text
account: 854847082059
principal: hr-traffic-provisioner
region: ap-south-1
```

The older readiness inventory in `AWS_SINGLE_EC2_RUNBOOK.md` describes account
`895469091637`; it is not the live LABS-08 runtime account.

## Observed resources

| Layer | Identity | State |
|---|---|---|
| EC2 | `i-0f8250d908737b568`, `triana-demo`, `t4g.small` | running, SSM online |
| RDS | `db-pg-1`, PostgreSQL 18.3 | available, private, encrypted |
| VPC | `vpc-04842890ff94f6fae` | EC2 and RDS attached |
| EC2 SG | `sg-040f622fca1f0fcea` | zero ingress |
| RDS SG | `sg-0132efc7294b9015c` | PostgreSQL from Triana host path |
| KMS | `alias/triana-artifacts` | present |
| App | `triana-app-1` | healthy when observed |
| Backend/DBOS | `triana-backend-1` | healthy when observed |

The operator profile cannot enumerate all S3 buckets, ECR repositories, tags,
IAM policies, or regions. Do not describe it as account administrator. The EC2
instance role owns the deployed runtime's scoped S3/KMS/ECR access.

## Local tunnels

The application ports remain private. Open two terminal sessions:

```text
/usr/local/bin/aws ssm start-session --profile akarsh-deepprobe \
  --region ap-south-1 --target i-0f8250d908737b568 \
  --document-name AWS-StartPortForwardingSession \
  --parameters portNumber=3000,localPortNumber=3000

/usr/local/bin/aws ssm start-session --profile akarsh-deepprobe \
  --region ap-south-1 --target i-0f8250d908737b568 \
  --document-name AWS-StartPortForwardingSession \
  --parameters portNumber=8000,localPortNumber=8000
```

Then use `http://127.0.0.1:3000/behavior` and
`http://127.0.0.1:8000/health/ready`.

## Legacy DBOS versus self-serve

“Legacy DBOS” is shorthand for the pre-auth LABS-08 operator route, not an old
DBOS version. It registers a pre-staged S3 trace, runs a foreground durable
workflow, stores facts/report artifacts in RDS/S3, and serves one configured
report. Its shipped HRAI compiler performs accounting only.

Self-serve added Supabase/OIDC authentication, personal workspaces, direct
PreviewTrace uploads, conversation browsing, and feature entitlements. In the
current composition, enabling OIDC selects self-serve mode and disables the
operator DBOS routes. The immediate TAU57 dry run deliberately proves the
non-auth analysis core first; joining authenticated uploads to workspace-safe
DBOS execution remains a separate security-sensitive slice.

## Safety

- Do not open EC2, app, backend, or PostgreSQL ingress.
- Do not copy `/opt/triana/*.env` values into this repository or command logs.
- Do not provision duplicate EC2/RDS/KMS resources while the observed stack is
  healthy.
- Deploy only digest-addressed images and preserve the existing rollback
  release metadata.
- Raw trace archives stay gitignored/private; only hash, counts, typed outcomes,
  and publication-safe projections enter Git.
