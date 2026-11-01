# Jobsworth technical design

**Status:** proposed, revision 0.3, 2026-11-01. **Runtime:** Python 3.14. See [terms](terms-of-reference.md), [ADR](adrs/adr-0001-scanner-and-policy-boundary.md), and [roadmap](roadmap.md).

## 1. Architecture

Jobsworth uses **Trivy** for dependency vulnerabilities and **Checkov** for configuration checks. It plans exact targets, resolves one coherent central-policy snapshot, collects immutable native JSON, evaluates scoped grants, and writes a decision sidecar plus coverage manifest. A passing result means the *declared* checks completed and no finding remains unaccepted; it is not a vulnerability-free certificate.

| Ecosystem | Scanner | Explicit limitation |
| --- | --- | --- |
| Rust | Trivy on Cargo.lock/manifests | No RustSec health or function-reachability claim |
| Python | Trivy on supported locked inputs, initially uv.lock | No implicit environment resolution |
| Go | Trivy module inputs | No vulnerable-symbol analysis |
| Bun, npm, pnpm | Trivy on supported text lockfiles | bun.lockb unsupported; no runtime bundle analysis |
| Terraform | Checkov static configuration | No provider/module advisory completeness |
| Ansible | Checkov selected rules | No Galaxy or managed-host vulnerability coverage |
| GitHub Actions | Checkov github_actions rules | No third-party action dependencies, remote workflow expansion, or repository-settings audit |

Each versioned profile specifies scanner version, expected inputs, selected checks, dependency groups, and required capabilities. A profile ships only after pinned scanner fixtures prove its claimed coverage. New/unconfigured inputs, unsupported formats, missing files, or ambiguous workspace ownership produce explicit incomplete status. Scan each Cargo workspace graph once, not once per member.

## 2. Trust and evidence

Use Cyclopts, pathlib, and the repository's cuprum executable-catalogue standard. Invoke scanners with argument vectors, pinned versions, controlled environments, timeouts, output limits, and no policy-controlled commands. Scanner output and repository content are untrusted data. Store reports outside the scanned tree and preserve raw bytes, SHA-256, diagnostics, source/input digests, scanner identity, policy revision, and UTC evaluation time.

A decision references a native report digest and unambiguous JSON pointer, never a fabricated permanent finding identity. Accepted findings remain visible. Coverage has independent `complete`, `partial`, or `failed` status per required capability. Exceptions cannot make incomplete coverage pass.

Trivy must not inherit ambient ignores or filters. Package grants require actual source-qualified identity; missing registry/Git revision is unknown, not an assumed public registry. Checkov's full JSON must retain passed, failed, skipped, and parsing-error records. Inline-skipped checks are **unevaluated**, not accepted; native skips or silently schema-rejected workflows make required coverage incomplete. Verify file processing and check execution against the accepted inventory rather than trusting exit zero.

## 3. Proposed consumer configuration

```toml
schema_version = 1
repository = "github.com/example/product"
local_exceptions = "jobsworth.exceptions.toml"

[authority]
repository = "example/security-policy"
ref = "main"
path = "jobsworth/policy.toml"
mode = "live"

[[targets]]
id = "rust-root"
path = "."
inputs = ["Cargo.toml", "Cargo.lock"]
profile = "cargo-locked-v1"
required_capabilities = ["dependency-vulnerabilities"]

[[targets]]
id = "workflows"
path = ".github/workflows"
inputs = [".github/workflows/ci.yml"]
profile = "github-actions-v1"
required_capabilities = ["workflow-configuration"]
```

Target IDs are display metadata, not authorization selectors. Identity binds canonical repository, exact target-root path, and versioned profile.

## 4. Exception and expiry semantics

Strict TOML ledgers have schema version, document type, namespace, and exception records. Active grants require ID, category, owner, reviewer, tracking issue, rationale, removal criteria, `created_at`, `reviewed_at`, `expires_at`, scope, and exact match. Reject unknown fields, duplicate IDs, empty selectors, invalid dates, and unsupported schemas.

Package matches require ecosystem, canonical name, **resolved source**, exact version(s), and advisory identifier. File matches require scanner-qualified rule ID, exact path, and SHA-256 of complete file bytes. A file grant knowingly accepts every occurrence of that rule in the unchanged file; line numbers and task names do not create a stable narrower identity.

```toml
schema_version = 1
document_type = "local-exceptions"
namespace = "local"
withdrawals = ["example-central:OLD-GRANT"]

[[exceptions]]
id = "EXAMPLE-WORKFLOW-001"
state = "draft"
category = "misconfiguration"
owner = "team:example"
reviewed_by = "team:example"
issue = "https://example.invalid/issues/1"
rationale = "Illustrative acceptance of this rule in the unchanged file."
removal_criteria = "Remove on correction, file change, or expiry."
created_at = "2026-11-01T00:00:00Z"
reviewed_at = "2026-11-01T00:00:00Z"
expires_at = "2026-12-01T00:00:00Z"

[exceptions.scope]
kind = "local"
target_paths = [".github/workflows"]
profiles = ["github-actions-v1"]

[exceptions.match]
identifier = "checkov:CKV_GHA_2"

[exceptions.match.subject]
type = "file"
path = ".github/workflows/ci.yml"
content_digest = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
```

This synthetic draft grants nothing. Require `created_at <= reviewed_at < expires_at`. Expiry is **exclusive**: at `now == expires_at`, the grant is invalid. Evaluate after scanning. Proposed lifetime ceilings are 90 days central and 30 days local from review, subject to pilot approval. Draft, withdrawn, and expired records never authorize. Every selector must be true; unknown source, scope, or graph evidence cannot authorize. Arrays are OR within a dimension, AND between dimensions.

## 5. Central Git authority

An external repository publishes an index and central ledgers:

```toml
schema_version = 1
namespace = "example-central"
exception_files = ["global.toml", "products.toml"]

[groups]
products = ["github.com/example/product", "github.com/example/worker"]

[guardrails]
allow_local_exceptions = true
max_exception_days = 90
max_local_exception_days = 30
```

Central scope is global, explicit repositories, or centrally defined groups, optionally restricted to exact target paths and profiles. Local scope inherits trusted repository identity. Resolve a live ref once to an immutable commit, retrieve every ledger at that commit, validate all records and groups, then publish atomically. A failed live authority lookup is incomplete even with a warm cache. Pinned mode documents delayed revocation; local-only mode is explicit and never an outage fallback.

Merge independently valid central and local grants additively, apply named local withdrawals, reject duplicate qualified IDs, and sort deterministically. Withdrawing one grant does not withdraw another overlapping grant. Deleting a central grant is not a subject prohibition; central guardrails can disable local grants. Subject bans and general local overrides are deferred.

## 6. Cargo ancestry

Where Axinite-style exceptions need it, obtain complete source-qualified Cargo metadata for the selected target, roots, features, and platform. `all_paths_through_any` means every root-to-vulnerable-package path crosses an approved ancestor. Remove approved ancestor nodes and search from all remaining roots; a surviving route is a counterexample. Cycles terminate through a visited set. Missing graph identity or incomplete context yields unknown. This proves dependency ancestry, **not** vulnerable-function unreachability. Preserve application-level removal tests during migration.

## 7. CI and failure semantics

The authoritative pull-request gate uses protected-base target configuration and local policy against proposed source content; a head-ledger proposal may be evaluated separately but cannot satisfy the required check. Never execute untrusted PR code with privileged pull_request_target credentials. Pin scanner artifacts, verify available digests, keep evidence in access-controlled CI artifacts, and redact publication separately from original bytes.

| Exit | Meaning |
| --- | --- |
| 0 | Required coverage complete, no blocking findings |
| 1 | Coverage complete, blocking findings |
| 2 | Required scan or live policy authority incomplete |
| 3 | Invalid configuration or policy |
| 4 | Internal error |
| 130 | Interrupted |

Interruption outranks internal error, invalid policy, incomplete coverage, and findings. Preserve all diagnostics even when only one exit code is returned.

Proposed CLI: `jobsworth discover`, `jobsworth policy check`, `jobsworth policy explain`, `jobsworth audit`, and `jobsworth explain OCCURRENCE`. None is implemented in the current scaffold.

## 8. Verification and migration

Use Hypothesis to test expiry boundaries, independent selector mismatches, additive merge permutation, duplicate IDs, authority failure, and non-authorization from unknown facts. Pin scanner conformance fixtures for clean/vulnerable inputs, unsupported formats, Checkov inline skips, parser failures, and schema-rejected GitHub workflows. Replay identical native evidence, policy, and evaluation time to prove deterministic decisions. Test the Cargo ancestry algorithm against an independent small-graph oracle.

Shadow-run against Podbot, Axinite, and Wildside before removing existing gates. Compare inventories, findings, accepted occurrences, coverage, and existing application-level removal conditions; equal exit codes are not sufficient. Preserve unsupported Rust health, Galaxy, provider, and action-dependency controls elsewhere.

## 9. Prior art and decisions

Trivy and Checkov supply scanning; Jobsworth supplies the small missing local/central expiry and decision contract. [ORT](https://oss-review-toolkit.org/ort/docs/configuration/resolutions) provides shared resolutions and [Dependency-Track](https://dependencytrack.org/) provides a service-based alternative. Neither justifies adding a hosted service now. Native ignore-file compilation is deferred because matching source, scope, and expiry exactly would require proving equivalence.

Sources: [Trivy coverage](https://trivy.dev/docs/latest/guide/coverage/language/), [Trivy filtering](https://trivy.dev/docs/latest/configuration/filtering/), [Checkov CLI](https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html), [Checkov GitHub Actions rules](https://github.com/bridgecrewio/checkov/blob/main/docs/5.Policy%20Index/github_actions.md), [Wildside contracts](https://github.com/leynos/wildside/blob/f682d1e47e4689ecb6a76fae05834c652b02baf6/tests/workflow_contracts/audit_exception_test.py), [Axinite guard](https://github.com/leynos/axinite/blob/fff22f8a137bcd01cba2b5729ae698afe41c2461/scripts/verify_audit_ignore_paths.py), [Podbot audit](https://github.com/leynos/podbot/blob/6e46a97fd0640bc7608674a31d5e05398da1afca/Makefile), and [typos-config-builder design](https://github.com/leynos/typos-config-builder/blob/ed29c47f3308a6197ebd5fe6be34e25442105963/docs/typos-config-builder-design.md).
