# ADR 0001: Scanner and policy boundary

## Status

Accepted 2026-11-01 for technology selection. Implementation remains proposed.

## Context

Existing Wildside, Axinite, and Podbot audits duplicate temporary-exception plumbing. Reimplementing package resolution, vulnerability databases, and configuration rules would duplicate mature software. Python 3.15 was originally requested, but uv support requires the current project to remain on Python 3.14.

## Decision

Use **Python 3.14**, **Trivy** for application dependency vulnerabilities, and **Checkov** for Terraform, Ansible, and GitHub Actions configuration findings. Run pinned scanners as external processes. Jobsworth retains native reports, merges local and central exceptions, evaluates expiry and exact scope after scanning, and independently reports coverage failures.

Cargo metadata may supply bounded dependency-ancestry evidence; it is not a third vulnerability scanner.

## Alternatives and consequences

Separate ecosystem-specific integrations increase maintenance. ORT and Dependency-Track remain viable if their broader compliance or service models become necessary. Native scanner ignores do not automatically preserve exact Jobsworth occurrence, source, and expiry semantics. Keep existing checks for capabilities outside the selected scanners; add no hosted service or generic plugin framework in v1.

See [design](../jobsworth-design.md) and [roadmap](../roadmap.md).
