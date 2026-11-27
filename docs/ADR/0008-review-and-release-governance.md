# ADR 0008: Deliver through small, traceable and reversible changes

- Status: Accepted
- Date: 2026-11-27

## Context

Kernel and runtime changes can have wide consequences. Large, mixed-purpose changes make review, rollback and fault isolation harder. The project's engineering playbook uses short-lived branches, pull requests, explicit checks and controlled release.

## Decision

- Keep the default branch releasable and use short-lived feature or documentation branches.
- Keep pull requests focused on a coherent outcome.
- Describe motivation, scope, risks, acceptance criteria, validation performed and limitations in every PR.
- Link relevant ADRs, issues and test evidence.
- Run automated checks and review the full diff before merging.
- Do not treat a successful bot status or merged PR as proof of independent review or runtime correctness.
- Use versioned releases and document compatibility or migration implications.
- Prefer reversible changes and define rollback or recovery steps for risky changes.

## Alternatives considered

- **Large implementation batches:** rejected because they are difficult to review and isolate.
- **Direct commits to the default branch for substantive changes:** rejected because they bypass the normal review and validation boundary.
- **Merge based only on green automation:** rejected because automated checks cannot evaluate every architectural or operational risk.

## Consequences

- More PRs and review steps are expected.
- Each change has clearer provenance and a smaller failure surface.
- Dependent work may be delivered as a sequence of linked PRs.

## Validation

- PRs include scope, acceptance criteria and actual test results.
- CI status is checked before merge.
- Release notes identify user-visible changes and known limitations.
- The default branch is checked after merge.
