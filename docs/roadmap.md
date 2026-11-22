# Jobsworth GIST roadmap

The [terms of reference](terms-of-reference.md) define goals G1–G6. The [design](jobsworth-design.md) defines the intended behaviour; [ADR 0001](adrs/adr-0001-scanner-and-policy-boundary.md) fixes Python 3.14, Trivy, and Checkov. **All tasks are pending.** Each phase tests an idea through review-sized tasks with explicit success conditions. There are no date commitments.

## 1. Prove scanner and policy contracts

**Idea:** Pinned scanner releases provide sufficient evidence for exact exception decisions and truthful coverage. Missing facts invalidate the affected capability rather than silently broadening grants.

### 1.1. Characterize native reports

- [ ] **1.1.1** Pin Trivy and collect Cargo/Python fixtures. **Success:** clean, vulnerable, development-dependency, unsupported-input, and ambiguous-source cases have reproducible native reports.
- [ ] **1.1.2** Pin Checkov and collect Terraform, Ansible, and GitHub Actions fixtures. **Success:** full JSON, inline skips, parser errors, schema rejection, and execution failures are observable or documented as blockers.

### 1.2. Establish policy validation

- [ ] **1.2.1** Implement strict versioned TOML/schema validation and `jobsworth policy check`. **Success:** unknown fields, duplicate IDs, invalid scope, malformed dates, and empty selectors fail.
- [ ] **1.2.2** Implement pure lifecycle and UTC evaluation. Requires 1.2.1. **Success:** draft, withdrawn, and expired grants cannot authorize; expiry is exclusive at the exact instant.

## 2. Deliver the first local audit

**Idea:** A small evaluator over native Trivy reports can accept one precise occurrence without accepting another version, source, or target.

### 2.1. Rust vertical slice

- [ ] **2.1.1** Collect bounded Trivy evidence for one Cargo graph. Requires 1.1.1. **Success:** reports are immutable and scanner failure, missing input, and truncation are incomplete.
- [ ] **2.1.2** Bind source-qualified Cargo identities to native findings. Requires 2.1.1. **Success:** ambiguous same-name/version occurrences cannot inherit one another's grants.
- [ ] **2.1.3** Implement local exception evaluation and `jobsworth audit`. Requires 1.2.2 and 2.1.2. **Success:** native evidence remains intact; coverage and findings produce distinct exit codes.

### 2.2. Python and explanation

- [ ] **2.2.1** Admit supported Python lockfiles and groups. Requires 2.1.3. **Success:** marker, group, local-source, and unsupported-generation cases have explicit outcomes.
- [ ] **2.2.2** Implement `jobsworth explain`. Requires 2.1.3. **Success:** every decision identifies original evidence, matching and rejected grants, owner, expiry, and removal criteria.

## 3. Compose central policy

**Idea:** One immutable Git authority snapshot, additive grants, and named local withdrawals cover the shared-policy requirement without a hosted service or general policy language.

### 3.1. Authority and freshness

- [ ] **3.1.1** Resolve one Git ref to a commit and validate the index and every ledger. Requires 1.2.1. **Success:** mixed revisions, invalid groups, duplicate paths, and partial fetches fail atomically.
- [ ] **3.1.2** Implement verified snapshot caching and live/pinned/local-only modes. Requires 3.1.1. **Success:** stale cache cannot satisfy live CI; pinned mode records delayed revocation.

### 3.2. Deterministic merge

- [ ] **3.2.1** Implement global, repository, and centrally defined group scopes. Requires 2.1.3 and 3.1.1. **Success:** unrelated repositories never receive scoped grants; ordering cannot change results.
- [ ] **3.2.2** Implement local grants, named withdrawals, and central guardrails. Requires 3.2.1. **Success:** overlapping grants remain visible, withdrawal affects only its named grant, and disabled local grants cannot authorize.
- [ ] **3.2.3** Exercise branch movement, expiry, outage, and revocation end to end. Requires 3.1.2 and 3.2.2. **Success:** each trust mode has the documented status and provenance.

## 4. Expand the supported ecosystems

**Idea:** Existing Trivy and Checkov readers can handle additional admitted input profiles without adding scanner-specific policy engines.

### 4.1. Dependency inputs

- [ ] **4.1.1** Add Go module profiles. Requires 2.2.1. **Success:** replacements and input-version differences remain visible without claiming symbol reachability.
- [ ] **4.1.2** Add npm and pnpm workspace/lockfile profiles. Requires 2.2.1. **Success:** development dependencies and ownership are tested; unsupported formats fail explicitly.
- [ ] **4.1.3** Add text Bun lockfile profiles. Requires 4.1.2. **Success:** bun.lock works under pinned fixtures; bun.lockb is rejected; advisory-wide historical ignores do not broaden grants.

### 4.2. Configuration inputs

- [ ] **4.2.1** Collect isolated Checkov Terraform reports. Requires 1.1.2. **Success:** selected rules and native skipped/error records remain visible.
- [ ] **4.2.2** Reconcile expected files and checks with Checkov output. Requires 4.2.1. **Success:** zero findings cannot hide an unevaluated input.
- [ ] **4.2.3** Implement exact rule/file/digest exceptions. Requires 4.2.2 and 2.1.3. **Success:** a one-byte file change invalidates acceptance.
- [ ] **4.2.4** Add Ansible profile. Requires 4.2.3. **Success:** playbook findings are attributable; Galaxy and managed-host gaps are disclosed.
- [ ] **4.2.5** Add GitHub Actions workflow profile. Requires 4.2.3. **Success:** .yml/.yaml files, reusable workflow definitions, native skips, and schema rejection are accounted for.
- [ ] **4.2.6** Document Actions coverage boundaries. Requires 4.2.5. **Success:** action dependencies and remote workflows are never implied by a configuration-only pass.

## 5. Trusted CI and migration

**Idea:** The same decisions survive protected-base CI enforcement and shadow comparisons without weakening existing gates.

### 5.1. CI boundary

- [ ] **5.1.1** Implement discovery and accepted-target reconciliation. Requires 4.1.3, 4.2.4, and 4.2.6. **Success:** missing/new inputs and ambiguous workspace ownership cannot produce an accidental empty pass.
- [ ] **5.1.2** Add trusted GitHub Actions invocation and evidence publication. Requires 3.2.3 and 5.1.1. **Success:** protected-base policy governs the required gate; untrusted PRs receive no privileged scanner credentials.

### 5.2. Preserve Rust provenance

- [ ] **5.2.1** Bind complete source-qualified Cargo metadata to the audited context. Requires 2.1.2. **Success:** missing roots, sources, or features make ancestry unknown.
- [ ] **5.2.2** Implement `all_paths_through_any` with counterexample paths. Requires 5.2.1. **Success:** an independent oracle agrees on cyclic, multi-root, and alternative-path graphs.

### 5.3. Migration and release

- [ ] **5.3.1** Test high-risk interactions across expiry, overlap, suppression, outage, and source mutation. Requires 3.2.3, 4.1.3, 4.2.6, 5.1.2, and 5.2.2. **Success:** all named failure combinations preserve the required nonzero status.
- [ ] **5.3.2** Shadow-run Podbot. Requires 5.3.1. **Success:** workspace and failure parity is documented before replacing its gate.
- [ ] **5.3.3** Shadow-run Axinite. Requires 5.3.1 and 5.2.2. **Success:** ancestry and dependency-health checks are retained or proven equivalent.
- [ ] **5.3.4** Shadow-run Wildside. Requires 5.3.1 and 4.1.3. **Success:** historical exceptions retain their dates and removal tests; no advisory-wide ignore silently expands.
- [ ] **5.3.5** Publish supported release matrix and operating guide. Requires 5.3.2–5.3.4. **Success:** Python 3.14, scanner pins, coverage gaps, retention, and measured overhead are documented.

## 6. Deferred decisions

**Idea:** Add new capabilities only when pilot evidence demonstrates a gap worth owning.

- [ ] **6.1.1** Decide whether third-party GitHub Action dependency auditing needs a separate capability. Requires 5.3.5. **Success:** a named consumer and reliable evidence source justify the proposal, otherwise it remains deferred.
- [ ] **6.2.1** Reassess native ignore export. Requires 5.3.5. **Success:** exact matching and expiry equivalence is demonstrated before using it for enforcement.
- [ ] **6.2.2** Reassess Dependency-Track/ORT adoption if portfolio requirements emerge. Requires 5.3.5. **Success:** measured operating costs and functions to retire justify any switch.
