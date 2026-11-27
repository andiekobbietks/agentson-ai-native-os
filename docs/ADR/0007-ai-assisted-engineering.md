# ADR 0007: Use AI assistance with human engineering accountability

- Status: Accepted
- Date: 2026-11-27

## Context

AI coding agents can accelerate research, design, implementation and review, but generated output may contain incorrect assumptions, insecure code, fabricated references or incomplete tests. The project itself explores agentic execution, so its development process must distinguish assistance from authority.

## Decision

- AI tools may assist with research, drafting, coding, test generation and review.
- Contributors must verify claims against primary sources and inspect generated changes.
- AI-generated code is treated as untrusted until reviewed and tested.
- Humans remain accountable for requirements, architecture decisions, licence compliance, security risk acceptance, approvals and releases.
- Agent instructions must be scoped, version-controlled and consistent with ADRs.
- Tool access and automated actions follow least privilege.
- Material AI-assisted changes must be reviewable from the diff and supporting evidence; no opaque bulk changes.

## Alternatives considered

- **Unreviewed autonomous merging:** rejected because it removes accountable review of risk and correctness.
- **Prohibit AI assistance:** rejected because assistance can be useful when bounded and verified.
- **Treat AI-generated tests as sufficient proof:** rejected because generated tests may encode the same mistaken assumptions as generated code.

## Consequences

- Human review remains a required delivery control.
- Contributor guidance must define permitted tools and boundaries.
- AI review output is advisory and does not replace test results or domain expertise.

## Validation

- PRs identify scope, tests and material risks.
- Reviewers inspect the complete diff, including generated files and workflows.
- Automated agents cannot approve or release their own changes without the repository's explicit human-controlled process.
