# Footprint Prediction Study (Part 1)

Can a coding task's footprint (files and Python symbols written, symbols read) be predicted from
the task text and the repository at its base commit, and what do predictions miss?
Static analysis, retrieval and evaluation only: no agents, no LLM calls, no GPU, and no code from
cloned repositories is ever executed. See `PRD.md` for the full spec and `PROTOCOL.md` for metrics.

## Run
```
cp .env.example .env   # fill GITHUB_TOKEN (read-only, public repos)
make setup             # uv sync + ENVIRONMENT.md
make test
```
Stages (`make data|split|resolve|extract|tasks|index|predict|eval|pilot`) land milestone by milestone.
`make test-eval CONFIRM=yes` is guarded and only runs after explicit human approval.

Layout: `src/fps/` library, `scripts/` thin CLIs, `configs/study.yaml`, `data/` (gitignored
clones and caches), `results/runs/<run_id>/` (derived data only).
