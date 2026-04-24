# Cloud cost tagging policy

Template. Copy this into your project's IaC or ops documentation and fill in the project-specific values.

---

## Required tags

Every cloud resource must have all four tags at creation. No tag = no deploy.

| Tag key | Required | Allowed values | Purpose |
|---------|----------|---------------|---------|
| `project` | Yes | `edgeflow`, `device-registry`, `platform` (enumerate your projects) | Which product this resource belongs to |
| `feature` | Yes | `telemetry-ingest`, `device-onboarding`, `api-gateway`, `shared` | Which feature within the project |
| `owner` | Yes | Engineer name or team name | Who is accountable for this resource's cost |
| `environment` | Yes | `prod`, `staging`, `dev`, `sandbox` | Deployment environment |

Optional but recommended:

| Tag key | Allowed values | Purpose |
|---------|---------------|---------|
| `cost-center` | e.g. `engineering`, `platform` | Finance attribution |
| `expires` | ISO date: `2026-12-31` | For temporary or sandbox resources |

---

## Tag value conventions

- Use lowercase with hyphens: `telemetry-ingest`, not `TelemetryIngest` or `telemetry_ingest`
- Use consistent project names: define the allowed list once and enforce it. Typos create orphaned cost attribution.
- `feature: shared` is allowed for resources shared across features (e.g. VPC, EKS control plane) — but keep these minimal. Shared resources obscure feature cost attribution.
- `environment: sandbox` is for individual engineer experiments. Sandbox resources must have an `expires` tag. Any sandbox resource without `expires` is treated as orphaned at the next monthly audit.

---

## Enforcement in Terraform

### Variable-based tag enforcement

```hcl
# variables.tf
variable "tags" {
  description = "Resource tags. All required tags must be present."
  type        = map(string)

  validation {
    condition = alltrue([
      contains(keys(var.tags), "project"),
      contains(keys(var.tags), "feature"),
      contains(keys(var.tags), "owner"),
      contains(keys(var.tags), "environment"),
    ])
    error_message = "Tags must include: project, feature, owner, environment."
  }

  validation {
    condition     = contains(["prod", "staging", "dev", "sandbox"], var.tags["environment"])
    error_message = "environment tag must be one of: prod, staging, dev, sandbox."
  }
}
```

```hcl
# main.tf — pass tags to every resource
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type
  tags          = var.tags
}

resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name
  tags   = var.tags
}
```

```hcl
# terraform.tfvars — set once per environment/feature
tags = {
  project     = "edgeflow"
  feature     = "telemetry-ingest"
  owner       = "alice"
  environment = "prod"
}
```

### AWS Tag Policy (optional — org-level enforcement)

If using AWS Organizations, define a tag policy to enforce required tags at the org level. This catches resources created outside Terraform (e.g. console, CLI).

```json
{
  "tags": {
    "project": {
      "tag_key": { "@@assign": "project" },
      "enforced_for": { "@@assign": ["ec2:instance", "rds:db", "s3:bucket"] }
    },
    "environment": {
      "tag_key": { "@@assign": "environment" },
      "tag_value": {
        "@@assign": ["prod", "staging", "dev", "sandbox"]
      },
      "enforced_for": { "@@assign": ["ec2:instance", "rds:db", "s3:bucket"] }
    }
  }
}
```

---

## Enforcement in Pulumi

```typescript
// policy/tagging-policy.ts
import * as pulumi from "@pulumi/pulumi";
import { PolicyPack, validateResourceOfType } from "@pulumi/policy";

const requiredTags = ["project", "feature", "owner", "environment"];
const allowedEnvironments = ["prod", "staging", "dev", "sandbox"];

new PolicyPack("tagging-policy", {
  policies: [
    {
      name: "required-tags",
      description: "All resources must have required tags.",
      enforcementLevel: "mandatory",
      validateResource: (args, reportViolation) => {
        const tags = (args.props.tags as Record<string, string>) || {};
        for (const tag of requiredTags) {
          if (!tags[tag]) {
            reportViolation(`Missing required tag: ${tag}`);
          }
        }
        if (tags.environment && !allowedEnvironments.includes(tags.environment)) {
          reportViolation(
            `Invalid environment tag: "${tags.environment}". Must be one of: ${allowedEnvironments.join(", ")}`
          );
        }
      },
    },
  ],
});
```

---

## How to use cost data after tagging is in place

### AWS Cost Explorer

1. AWS Console → Cost Explorer → Group by: Tag → select `feature`
2. View gives per-feature cost automatically
3. Add a second grouping by `environment` to separate prod vs dev spend
4. Save this view and check it at every monthly audit

### GCP Billing labels

GCP uses "labels" (same concept as AWS tags). Same required labels apply. View in Billing → Reports → Group by → Label.

### Azure tags

Same concept. View in Cost Management → Cost analysis → Group by → Tag.

---

## Exception process

Some resources cannot be tagged (e.g. some managed services, third-party integrations, billing-level items like data transfer).

For untaggable resources:
1. Document the exception in a comment in the IaC code
2. Note the approximate cost in the comment
3. Assign it manually to the correct feature in a cost allocation spreadsheet (checked monthly)
4. Raise an issue with the cloud provider if the resource type should support tags but does not

Do not silently omit tags. If a resource cannot be tagged, it must be explicitly documented.

---

## Sandbox cleanup policy

Sandbox resources with an `expires` tag past its date are automatically scheduled for review at the next monthly audit. Engineers are responsible for:
- Extending the `expires` tag if the resource is still needed
- Terminating the resource if it is no longer needed

Sandbox resources without an `expires` tag are treated as orphaned and will be flagged for deletion at the monthly audit without prior notice.
