# Jobsworth: terms of reference

**Status:** proposed. **Date:** 2026-11-01.

## Problem

Repository maintainers need to distinguish unaccepted security findings, temporarily accepted risk, and scans that never completed. Wildside records exception lifecycles and removal conditions; Axinite checks dependency ancestry; Podbot audits Cargo workspaces; typos-config-builder demonstrates centrally managed policy with local overlays. Jobsworth consolidates reusable policy behaviour, not scanning intelligence.

## Users

Repository maintainers run local and CI gates. Central policy maintainers publish global and repository/group-scoped exceptions. Reviewers reconstruct ownership, justification, expiry, and original evidence. A hosted portfolio dashboard is not an initial requirement.

## Goals and acceptance

| Goal | Testable outcome |
| --- | --- |
| G1: Accountable acceptance | Every accepted occurrence resolves to an unchanged native report and a reviewed grant with owner, issue, rationale, removal condition, and expiry |
| G2: Deterministic composition | Central and local grants merge regardless of file ordering; named withdrawals and overlapping grants remain explainable |
| G3: Bounded lifetime | A grant stops applying exactly at its UTC expiry; stale live central policy cannot authorize |
| G4: Honest coverage | Missing inputs, scanner errors, native skips, and unprocessed workflows cannot produce a passing gate |
| G5: Ecosystem support | Rust, Python, Go, Bun/npm/pnpm, Terraform, Ansible, and GitHub Actions have pinned-version fixtures and documented limitations |
| G6: Safe migration | Wildside, Axinite, and Podbot shadow runs reconcile findings and existing controls before replacement |

## Constraints

Implement in **Python 3.14** using **Trivy and Checkov** as the scanning engines. Use an external Git repository for centrally managed global and scoped exceptions, with repository-local grants and withdrawals. Run without a Jobsworth hosted service. No implicit dependency installation, Terraform plan/apply, playbook execution, or workflow execution.

The first release covers dependency vulnerabilities and selected configuration findings. It does not claim code reachability, provider/module advisories, Galaxy collection vulnerabilities, managed-host scanning, third-party GitHub Action dependencies, or complete remote reusable-workflow analysis. Do not build a general policy language, new vulnerability database, or portfolio inventory.

## Assumptions and unresolved decisions

Trusted CI supplies accepted repository identity, scanner pins, and target configuration; repository review governs policy changes. Reviewer strings are not authenticated approvals. Pilot evidence must determine supported OS/architecture matrix, scanner versions and rule profiles, retention, scan overhead, and whether proposed 90-day central and 30-day local exception limits are suitable.

## Handoff

The [technical design](jobsworth-design.md) specifies contracts. The [GIST roadmap](roadmap.md) maps goals to implementation and migration. [ADR 0001](adrs/adr-0001-scanner-and-policy-boundary.md) records the selected boundary.
