# Contributing

## Ground rules

- Prefer small, reviewable changes.
- Record architecture decisions in `docs/ADR/`.
- Do not claim a feature is implemented until its test evidence exists.
- Keep third-party code, assets, models and datasets subject to their own licences.
- Never import code from restricted or unavailable upstream repositories.

## Development sequence

1. Read `docs/ARCHITECTURE.md` and `docs/VALIDATION.md`.
2. Create or update a test before claiming a new capability.
3. Record toolchain versions and exact commands.
4. Run the relevant test suite and include results in the pull request.
5. Update the validation matrix and known limitations.

## Source reuse

Before adapting external code, record its repository URL, exact commit SHA, file paths, licence and required notices in `docs/RESEARCH.md`. Do not assume the top-level repository licence applies to every dependency or asset.
