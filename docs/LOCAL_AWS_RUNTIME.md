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

## IAM required for the launch path

Do not attach `AdministratorAccess`. Use the following split for the current
account and resources. Database credentials and PostgreSQL grants remain in
the runtime environment; they are not IAM permissions.

### Operator/deployer: `hr-traffic-provisioner`

The operator uploads only to `staging/`, pushes images, inspects or starts the
existing EC2/RDS resources, and operates the private host through SSM.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InspectExistingCompute",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "rds:DescribeDBInstances"
      ],
      "Resource": "*"
    },
    {
      "Sid": "OperateExistingCompute",
      "Effect": "Allow",
      "Action": ["ec2:StartInstances", "ec2:StopInstances"],
      "Resource": "arn:aws:ec2:ap-south-1:854847082059:instance/i-0f8250d908737b568"
    },
    {
      "Sid": "OperateExistingDatabase",
      "Effect": "Allow",
      "Action": ["rds:StartDBInstance", "rds:StopDBInstance", "rds:RebootDBInstance"],
      "Resource": "arn:aws:rds:ap-south-1:854847082059:db:db-pg-1"
    },
    {
      "Sid": "RunCommandsOnTrianaHost",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": [
        "arn:aws:ec2:ap-south-1:854847082059:instance/i-0f8250d908737b568",
        "arn:aws:ssm:ap-south-1::document/AWS-RunShellScript"
      ]
    },
    {
      "Sid": "ReadCommandResults",
      "Effect": "Allow",
      "Action": ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations", "ssm:CancelCommand"],
      "Resource": "*"
    },
    {
      "Sid": "OpenPrivatePortForwarding",
      "Effect": "Allow",
      "Action": "ssm:StartSession",
      "Resource": [
        "arn:aws:ec2:ap-south-1:854847082059:instance/i-0f8250d908737b568",
        "arn:aws:ssm:ap-south-1::document/AWS-StartPortForwardingSession"
      ]
    },
    {
      "Sid": "ManageOwnSessions",
      "Effect": "Allow",
      "Action": ["ssm:ResumeSession", "ssm:TerminateSession"],
      "Resource": "arn:aws:ssm:ap-south-1:854847082059:session/${aws:username}-*"
    },
    {
      "Sid": "ListTrianaStaging",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::triana-artifacts-854847082059-ap-south-1",
      "Condition": {"StringLike": {"s3:prefix": ["staging/*"]}}
    },
    {
      "Sid": "ManageTrianaStagingObjects",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:GetObjectAttributes", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::triana-artifacts-854847082059-ap-south-1/staging/*"
    },
    {
      "Sid": "UseTrianaKmsForStaging",
      "Effect": "Allow",
      "Action": ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
      "Resource": "arn:aws:kms:ap-south-1:854847082059:key/500e1fbf-dea4-48ac-87dd-560ccea889ca",
      "Condition": {"StringEquals": {"kms:ViaService": "s3.ap-south-1.amazonaws.com"}}
    },
    {
      "Sid": "GetEcrLogin",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "PushAndInspectTrianaImages",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:DescribeImages",
        "ecr:DescribeRepositories",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": [
        "arn:aws:ecr:ap-south-1:854847082059:repository/triana/backend",
        "arn:aws:ecr:ap-south-1:854847082059:repository/triana/app"
      ]
    }
  ]
}
```

### EC2 runtime: `triana-demo-ec2-role`

Keep `AmazonSSMManagedInstanceCore` attached. Add this application policy so
the backend can read staged input, publish immutable objects, and use the
bucket KMS key. It intentionally does not grant arbitrary bucket access.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListTrianaRuntimePrefixes",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::triana-artifacts-854847082059-ap-south-1",
      "Condition": {
        "StringLike": {"s3:prefix": ["staging/*", "objects/sha256/*", "runs/*"]}
      }
    },
    {
      "Sid": "ReadStagedSources",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:GetObjectAttributes"],
      "Resource": "arn:aws:s3:::triana-artifacts-854847082059-ap-south-1/staging/*"
    },
    {
      "Sid": "PublishAndReadImmutableArtifacts",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:GetObjectAttributes"],
      "Resource": [
        "arn:aws:s3:::triana-artifacts-854847082059-ap-south-1/objects/sha256/*",
        "arn:aws:s3:::triana-artifacts-854847082059-ap-south-1/runs/*"
      ]
    },
    {
      "Sid": "UseTrianaArtifactKeyThroughS3",
      "Effect": "Allow",
      "Action": ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
      "Resource": "arn:aws:kms:ap-south-1:854847082059:key/500e1fbf-dea4-48ac-87dd-560ccea889ca",
      "Condition": {"StringEquals": {"kms:ViaService": "s3.ap-south-1.amazonaws.com"}}
    },
    {
      "Sid": "GetEcrLogin",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "PullTrianaImages",
      "Effect": "Allow",
      "Action": ["ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"],
      "Resource": [
        "arn:aws:ecr:ap-south-1:854847082059:repository/triana/backend",
        "arn:aws:ecr:ap-south-1:854847082059:repository/triana/app"
      ]
    }
  ]
}
```

For the fastest current launch, if images must continue to be built on the
EC2 host, temporarily add the operator policy's `PushAndInspectTrianaImages`
actions to `triana-demo-ec2-role`. Remove that temporary statement after a CI
builder or working operator Docker daemon owns image builds. Do not grant the
runtime role general ECR or S3 administration.

No Terraform provisioning permissions are required for this launch because
EC2, RDS, networking, S3, KMS, ECR, and SSM already exist. If replacement
infrastructure is later approved, create a separate plan-specific provisioner
role after reviewing the Terraform plan; do not add open-ended EC2, IAM, or
CloudFormation permissions to either principal above.

## Deployed TAU57 private canary

Observed live on 2026-08-06:

```text
release: 0d4407946d86ef0d9888de2fb961ded4b51b8156
backend: sha256:c24dc75b3359c39c0afe2e7ddf1ce80c2a423447bbfa566df3ff04060d753c38
app: sha256:8b54879a915764e2bc23966188c70bf4215f3c72433679a8ccccf3edf40f169c
import: imp_37e742f4d6947028cd167c4a52478c50
run: run_6e99b23c29175715b5d1ba5a18761b4c
report: rpt_70718d7e6cfe538b5a99bc4a44bb536c
```

The app and backend are healthy, RDS is at Alembic 0003, and `/behavior`
renders 54 deterministic structural groups over 57 accepted synthetic traces.
Local SSM tunnels expose the private endpoints at
`http://127.0.0.1:3000/behavior` and `http://127.0.0.1:8000` while their
sessions remain open.

The temporary `PushTrianaImages`/`TrianaTemporaryEcrPush` statement on
`triana-demo-ec2-role` is no longer required after this deployment and should
be removed. Keep the runtime pull and artifact policies.
