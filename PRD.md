# PRD: Footprint Prediction Study (Part 1) — Setup Guide for Claude Code

Oct 18, 2026 · @M.Taaha

## 1. Context: what we are doing and why

You (Claude Code) are setting up a local, reproducible pipeline for Part 1 of a research study: measuring how well a coding task's footprint can be predicted before any agent works on it.

**The problem.** When several LLM coding agents work on one repository in parallel, each builds on code it read earlier. If another agent changes that code first (for example, renames a function), the two patches can merge cleanly as text yet break together. We call these stale-premise conflicts; the software-engineering literature calls them build or semantic conflicts.

**Where existing work stops.** Recent systems schedule or guard parallel agents, but each assumes something we want to measure:

- NP-Bench / Nerveplane plans parallel work from each task's declared scope (files it writes, contracts it consumes). Its scopes are hand-written, and its authors call automatic scope inference unbuilt work.
- STORM validates agent writes at file granularity; CoAgent relies on the agent's own judgment of what a change affects.
- Co-Coder partitions greenfield projects using a dependency graph produced by an LLM-generated blueprint.

**The Part 1 question.** Can a task's footprint be predicted automatically from the task text and the repository at its base commit, and what do predictions systematically miss?

**Footprint, defined.**

- Write set: files, and Python symbols (functions, classes, methods), that the change adds, modifies, deletes or renames.
- Read set: symbols referenced by the changed code, resolved to their definitions where possible.

**Example.** The task text is “Rename `parse_price` to `parse_amount` and update its callers.” The repo has `utils.py`, `checkout.py`, `cart.py` and `tests/test_utils.py`.

1. Predict: using only that sentence and the repo at the base commit, a predictor ranks `utils.py`, `checkout.py`, `cart.py`.
2. Ground truth: the real PR changed `utils.py`, `checkout.py` and `tests/test_utils.py`.
3. Score: two of the three real files are in the top three, so file recall@3 is 2/3. The missed test file is the kind of systematic miss RQ3 categorizes.

At symbol level, the prediction should include `parse_price` as written and its callers as read.

**Why it matters.** With footprints known up front, tasks whose footprints overlap can be kept from running at the same time, or run in a set order. Planners such as NP-Bench already do this, but with hand-written footprints. If prediction works, up-front scheduling becomes practical; if not, detection at commit time is the fallback. “Before any agent works on it” means the predictor never sees the finished patch.

**Data.** Real agent-authored pull requests from the AIDev dataset, restricted to Python repositories. Ground truth is each PR's actual diff, computed with git.

**What Part 1 is not.** No agents run, no LLM calls, no GPU, and no code from cloned repositories is ever executed. It is static analysis, retrieval and evaluation, on a CPU, on the human's machine.

## 2. Goals, non-goals and research questions

The goal is a resumable local pipeline that produces three things: a ground-truth footprint dataset for a sample of Python agent PRs, deterministic baseline predictions, and an evaluation report on the dev split. The test split stays untouched until the human approves.

**Research questions**

| ID | Question |
| --- | --- |
| RQ1 | File level: how accurately do deterministic methods predict the files a task changes, given only pre-work task text and the repo at the base commit? |
| RQ2 | Symbol level: the same for symbols written, and for the internal symbols the change depends on. |
| RQ3 | Misses: which categories are systematically missed (new files, tests, config, renames, dynamic references, files outside the import graph)? |
| RQ4 | Input text: how much do results change between title only, title plus linked issue, and PR body (a leaky upper bound, written after the work)? |

**Non-goals for this phase**

- Building an orchestration system or running coding agents.
- LLM-assisted predictors. These come later as Part 1b, behind a human checkpoint.
- Executing tests, installing repo dependencies, or building merged trees.
- Any GPU, cloud, Docker or VM setup.

## 3. Hard rules for Claude Code

These rules override convenience. If a step seems to require breaking one, stop and ask the human.

1. **Never execute code from cloned repositories.** No installing their requirements, running their tests, importing their modules or running their setup scripts. Read files as blobs with `git show` and parse them with Python's `ast`. If a name resolver is added later, first verify it does not import or execute project code.
2. **Secrets.** Use a fine-grained, read-only GitHub token from the `GITHUB_TOKEN` environment variable. Never write it to files, logs or commits. Keep `.env` in `.gitignore` and commit only `.env.example`.
3. **Frozen split.** Create the dev/test split by repository once, with a fixed seed, before writing any predictor. Record its hash. Never load test-split ground truth during development. Test evaluation runs only via `make test-eval CONFIRM=yes`, after explicit human approval.
4. **Protocol first.** Metrics and decision rules live in `PROTOCOL.md`. Never change them after results exist without human approval. Log every change there with the date and reason.
5. **Determinism.** Fixed seeds, `PYTHONHASHSEED=0`, and all iteration sorted by stable keys (files, PRs, symbols). Ties break by ID. No wall-clock time in any decision logic.
6. **Resumability.** Every long step writes append-only JSONL keyed by a stable ID and skips completed keys on rerun. Never delete results to start fresh without asking.
7. **Attrition.** Count items entering and leaving every filter and failure path, and report the denominators.
8. **Licensing.** Never commit repository source code, patches or diffs to this project. Store derived data only (paths, symbol names, metrics) plus IDs. Clones and caches stay in the gitignored `data/` directory.
9. **Pinned versions.** Record the Python version, lockfile hash, dataset revision and git version in every run's manifest.
10. **Checkpoints.** At each checkpoint in Section 6, summarize what was done and what was found, then wait for the human.
11. **Ask before** deleting data, scaling beyond the pilot, changing the protocol, adding dependencies with network or execution side effects, or spending money.
12. **Inspect, don't assume.** Before using any dataset table, print its schema and a few example rows. Never guess column names.

## 4. Environment setup

Everything runs locally on CPU. Set it up in this order and record every version in `ENVIRONMENT.md`.

1. **Detect the OS.** On Windows, set up WSL2 with Ubuntu and keep the project and data inside the Linux filesystem (for example `~/footprint-study`), never under `/mnt/c`. Windows path-length limits, case-insensitive names and symlinks in cloned repos cause failures. On macOS or Linux, work natively.
2. **Git.** Run `git --version`. Milestone 5 uses `git merge-tree --write-tree`, which is believed to need git 2.38 or newer. Verify this against the git documentation and upgrade if needed.
3. **Python.** Pin one version (3.11 is a safe default) with `uv` (preferred) or `venv` plus `pip-tools`. Commit the lockfile.
4. **Packages.** Start with: `pandas`, `pyarrow`, `huggingface_hub`, `requests`, `rank-bm25`, `networkx`, `numpy`, `scikit-learn`, `pyyaml`, `tqdm`, `pytest`, `ruff`. Resolve imports with your own `ast`-based resolver first. Add others only with a stated reason in the commit message.
5. **Tokens.** Create a GitHub fine-grained token with read-only access to public repositories and export it as `GITHUB_TOKEN`. A Hugging Face token is needed only if the dataset requires login.
6. **Resources.** Report free disk and RAM. Read large parquet files with column selection or batch streaming, never whole. Estimate disk needs from the pilot before scaling.
7. **Record.** Write `ENVIRONMENT.md` with OS, CPU, RAM, free disk, git version, Python version and lockfile hash.

## 5. Repository layout and conventions

Use this layout so every step has one obvious home.

```
footprint-study/
  README.md          # what this is and how to run it
  PRD.md             # this document
  PROTOCOL.md        # research questions, metrics, decision rules (human-owned)
  ENVIRONMENT.md     # recorded machine and versions
  CHANGELOG.md       # one entry per milestone
  Makefile
  pyproject.toml
  uv.lock
  .env.example       # GITHUB_TOKEN= (no real values)
  .gitignore         # data/, .env, caches
  configs/
    study.yaml       # paths, seeds, filters, k values, dataset revision
  src/fps/
    data/            # dataset download, manifest, filters, split
    gitops/          # clone, fetch PR refs, base resolution, diffs
    extract/         # ground-truth footprints (files, symbols, dependencies)
    tasks/           # task-text variants
    index/           # repo snapshot indexing (files, symbols, import graph)
    predict/         # baseline predictors
    eval/            # metrics, bootstrap, miss categories, report
    util/            # logging, IDs, resumable JSONL, hashing
  scripts/           # thin CLIs that call src/fps
  tests/
    fixtures/        # tiny synthetic git repos built during test setup
  data/              # gitignored: raw/, clones/, cache/
  results/
    runs/<run_id>/   # manifest.json, *.jsonl, report.md (derived data only)
```

**Conventions**

- `run_id` = UTC timestamp plus short code commit hash. Each run's `manifest.json` records the config hash, code commit, dataset revision, versions and counts.
- `pr_key` = `<owner>/<repo>#<pr_number>`, used as the key in every JSONL file.
- Make targets: `setup`, `data`, `split`, `resolve`, `extract`, `tasks`, `index`, `predict`, `eval`, `pilot`, and the guarded `test-eval`.
- Commit `manifest.json` and `report.md`. Commit JSONL results only if small and free of code or patch text; otherwise keep them under `data/`.
- Type hints, `ruff`, and `pytest` throughout. The extractor and metrics must have unit tests.
- End each milestone with a commit and a `CHANGELOG.md` entry.

## 6. Milestones, acceptance criteria and checkpoints

Work through these in order. Each ends with a commit; the three checkpoints (A, B, C) are hard stops where the human decides.

1. **M0 — Scaffold and environment.**
   - Create the layout in Section 5 and the environment in Section 4.
   - Write `README.md`, `configs/study.yaml` (defaults in Section 7) and a `PROTOCOL.md` template copying Sections 2 and 8, with threshold cells left blank.
   - Done when `make setup` works from a fresh clone, `pytest` runs, and `ENVIRONMENT.md` is filled.
   - **Checkpoint A:** the human fills the decision thresholds in `PROTOCOL.md` and answers the open questions in Section 9.
2. **M1 — Dataset and manifest.**
   - Read the AIDev dataset card(s) and agree a version with the human. Pin its revision hash in `study.yaml`.
   - Print the schema and sample rows of every table used. Load only needed columns, streaming large files.
   - Join PRs to repositories and apply config filters: primary language Python, minimum stars, PR state, maximum files changed, valid repo URL.
   - Write `data/manifest.jsonl` and an attrition table (count after each filter).
   - Done when a rerun reproduces the same manifest hash.
3. **M2 — Frozen split.**
   - Group PRs by repository. Assign repositories to dev and test with the configured seed and fraction.
   - Draw the pilot sample (default 50 PRs) from dev only, stratified by agent where possible.
   - Write `splits.json`, record its hash, and add a loader guard that refuses test PRs unless `CONFIRM=yes`.
   - Done when the split hash is recorded and a unit test shows the guard works.
4. **M3 — Base and head resolution.**
   - Partial-clone each repo once (`git clone --filter=blob:none`) into `data/clones/`, reusing clones.
   - Fetch `refs/pull/<n>/head` for the PR head commit.
   - Base commit = `git merge-base` of the PR head and the PR's base SHA from the GitHub REST API (cached under `data/cache/github/`). Fallback: merge-base with the default branch. Record which method was used.
   - Classify failures (deleted ref, no merge base, repo unavailable, API error), skip them, and count them.
   - Back off on rate limits; the step must resume after interruption.
   - Done when pilot resolution rates and failure categories are reported.
5. **M4 — Ground-truth extractor.**
   - Files: `git diff --name-status -M <base> <head>` gives each file's status (added, modified, deleted, renamed).
   - Python symbols: read base and head versions with `git show`, parse with `ast`, map changed line ranges to enclosing definitions, and record symbols added, modified or deleted by qualified name, with a signature-change flag.
   - Dependencies: names referenced in changed or added code, resolved through the repo's own imports to a defining file and symbol. Mark the rest as external or unresolved; never guess.
   - Non-Python files: file level only, categorized as test, config, docs or other.
   - Unit tests on synthetic fixture repos built during test setup: add a function, edit a body, rename a function and its caller, delete, change a signature, add a file, rename a file, change a non-Python file. Assert the expected footprints.
   - Cross-check pilot file lists against the GitHub API's list of PR files and report the agreement rate.
   - Write `review_sheet.md`: 20 random pilot PRs, each with its PR link and extracted files and symbols.
   - **Checkpoint B:** the human spot-checks the review sheet. No predictor is built until the human accepts the extractor.
6. **M5 — Tooling validation (recommended, non-blocking).**
   - Download the Xu et al. replication package (links in Section 10) and replay a random subset of about 50 of their PR pairs with the M3 tooling plus `git merge-tree --write-tree`.
   - Report agreement with their conflict labels and investigate disagreements. If the package is unavailable or its format differs, report that and move on.
7. **M6 — Task-text variants.**
   - For each PR build: (a) title only; (b) title plus linked issue text where one exists; (c) title plus PR body, labelled a leaky upper bound because the body is written after the work.
   - Find linked issues from the dataset's issue tables first; otherwise parse issue references from the PR, using the body only to find the reference, never as variant (b) text.
   - Done when the variants are stored with an availability count per variant.
8. **M7 — Repository snapshot index.**
   - At each base commit, read files through git without checking out or executing anything. Exclude vendored and generated directories per config.
   - Build per-file search text (path tokens, identifiers, docstrings), a symbol table, a module import graph and name-based call references.
   - Cache per (repo, base commit). Done when the pilot index rebuilds to the same hash.
9. **M8 — Baseline predictors.** Each produces ranked files and ranked symbols per PR and per text variant.
   - P0: seeded random ranking (a floor).
   - P1: path heuristic matching text tokens to file and module names.
   - P2: BM25 over files.
   - P3: BM25 over symbols, aggregated to files.
   - P4: P2 or P3 plus import and call-graph expansion with decay. Tune its parameters on dev only.
   - Done when pilot predictions exist and a rerun produces identical output hashes.
10. **M9 — Evaluation and report (dev only).**
    - Compute the Section 8 metrics with repository-clustered bootstrap intervals, plus the miss categories and attrition.
    - Write `report.md` with one table per research question.
    - **Checkpoint C:** the human reviews pilot results, runtime and disk use, then decides to scale, adjust or stop.
11. **M10 — Scale the dev set (after approval).** Run the same pipeline on the full dev split and regenerate the report.
12. **M11 — Final test evaluation (after explicit approval).** Freeze the code commit, run `make test-eval CONFIRM=yes` once, and report. No tuning afterwards.

## 7. Data schemas and configuration

Every JSONL record carries `pr_key`. Field names below are the contract between stages; source column names from AIDev must be confirmed by inspection (Rule 12).

| File | Fields |
| --- | --- |
| `manifest.jsonl` | pr\_key, repo\_full\_name, pr\_number, agent, state, created\_at, merged\_at, repo\_stars, repo\_language, dataset\_revision, split, pilot |
| `resolution.jsonl` | pr\_key, head\_sha, base\_sha, base\_method (api\_merge\_base or default\_branch\_merge\_base), status (ok, deleted\_ref, no\_merge\_base, repo\_unavailable, api\_error), error |
| `footprints.jsonl` | pr\_key, base\_sha, head\_sha, files \[path, status, old\_path, kind\], symbols\_written \[qualname, file, change, signature\_changed\], symbols\_read \[name, resolved\_qualname, file, kind: internal, external or unresolved\], stats \[n\_files, n\_py\_files, n\_symbols\_written, parse\_errors\] |
| `tasks.jsonl` | pr\_key, variant (title, title\_issue, title\_body), text, available, source |
| `predictions.jsonl` | pr\_key, variant, predictor, params\_hash, files\_ranked, symbols\_ranked |
| `metrics.jsonl` | predictor, variant, level, metric, k, value, ci\_low, ci\_high, n |

**Default `configs/study.yaml`** (values are starting defaults the human may change at Checkpoint A):

```yaml
dataset:
  hf_repo: hao-li/AIDev          # confirm version with the human
  revision: "<pinned-commit-hash>"
filters:
  language: Python
  min_stars: 100
  pr_states: [merged]
  max_files_changed: 50
split:
  seed: 20261018
  test_fraction: 0.3
  pilot_size: 50
git:
  clone_filter: blob:none
  clones_dir: data/clones
github:
  token_env: GITHUB_TOKEN
  cache_dir: data/cache/github
index:
  exclude_dirs: [vendor, third_party, node_modules, build, dist, .venv, site-packages]
predict:
  k_values: [1, 3, 5, 10]
  graph_hops: 1
eval:
  bootstrap_resamples: 1000
  bootstrap_unit: repository
```

## 8. Evaluation metrics and decision rules

The metrics are fixed here. The thresholds are blank on purpose: the human fills them in `PROTOCOL.md` at Checkpoint A, before any results exist. Claude Code reports numbers; the human decides.

**Metrics**

- File level: precision@k and recall@k for k in {1, 3, 5, 10}; R-precision (recall at k equal to the true number of files); mean reciprocal rank of the first correct file.
- Symbol level: the same metrics for symbols written, plus recall of internal symbols read.
- Every metric reported per predictor and per text variant, with 95% intervals from a bootstrap that resamples repositories, not PRs.
- Misses: the share of missed ground-truth files by category (new file, test, config or docs, renamed, outside the import graph of the top predictions, non-Python).
- Coverage: PRs entering and leaving each stage, with reasons.

**Decision rules (thresholds set by the human)**

| Question | Rule | Threshold |
| --- | --- | --- |
| Is the ground truth trustworthy? | Human spot-check agreement on the 20-PR review sheet | \_\_\_ of 20 |
| Does the extractor match GitHub? | Pilot file-list agreement with the GitHub API | \_\_\_ % |
| Is prediction good enough to continue to Part 2? | Best deterministic predictor's file recall@5 on the title-plus-issue variant | \_\_\_ |
| Does graph expansion help? | P4 minus P2 file recall@5, interval excluding zero | yes / no |
| How much does the PR body leak? | Title-plus-body recall@5 minus title-plus-issue recall@5 | \_\_\_ |

## 9. Risks, data caveats and open questions

The biggest risk is a wrong ground truth, which is why Checkpoint B gates everything after it.

| Risk | Effect | Mitigation |
| --- | --- | --- |
| AIDev patch data is incomplete: large patches are missing, and patches are masked where licences forbid redistribution | Footprints from dataset patches would be wrong | Use git diffs as ground truth; dataset patches only for cross-checks |
| The popular-subset definition differs (dataset card: over 100 stars; original paper: 500 or more) | Sample depends on which version is used | Filter explicitly on the stars field; record the threshold |
| Dataset versions differ greatly in size; the largest files are several GB | Memory blowups, irreproducible samples | Pin a revision; select columns and stream |
| Deleted PR refs and missing merge bases | Attrition | Log every failure; Xu et al. lost 31 of 747 pairs this way |
| The PR body describes the finished change | Inflated results | Report the body variant only as a labelled upper bound |
| One merged patch is only one valid solution | Predictions can be judged wrong when fine | State it as a limitation; multiple agent runs per task belong to Part 2 |
| Dynamic Python (`getattr`, monkeypatching, star imports) | Missed dependencies | Record as unresolved; never guess |
| Merged PRs were already reviewed | Selection bias | Note it; closed-unmerged PRs can be a later stratum |
| Vendored or generated files | Inflated footprints | Exclusion list in config; report its effect |
| The field moves monthly | Overlap with new papers | Re-check arXiv before writing up |

**Open questions for the human (answer at Checkpoint A)**

- [ ] Which AIDev version and revision to pin?
- [ ] Merged PRs only, or include closed-unmerged?
- [ ] Minimum stars and maximum PR size?
- [ ] Which OS (is WSL2 needed)?
- [ ] Decision thresholds in Section 8.

## 10. Out of scope (Part 2) and references

Part 2 starts only after Checkpoint C and needs sandboxed execution, model access and a budget, none of which Part 1 sets up.

**Out of scope now:** running coding agents; LLM-assisted predictors (Part 1b); executing tests or building merged trees; Docker, VMs, GPU or cloud; planner sensitivity experiments; live timing-versus-specificity ablations.

**Read during this research**

- [Xu, Subramanian and Karthik (2026), AI Agent Pull Requests on GitHub](https://arxiv.org/html/2607.04697v2): textual conflict rates among co-active agent PRs; method for fetching PR refs and merge-bases. Replication package: [GitHub](https://github.com/Quantum535/concurrent-agentic-prs-replication), [Zenodo](https://doi.org/10.5281/zenodo.21186464).
- [NP-Bench and Nerveplane (2026)](https://arxiv.org/pdf/2610.07261): scheduling parallel agents from declared scopes; code at [Nerveplane](https://github.com/sumanyumuku98/Nerveplane).
- [STORM (2026)](https://arxiv.org/pdf/2605.20563): file-level write-time validation; code at [STORM](https://github.com/dreamyang-liu/STORM).
- [CoAgent (2026)](https://arxiv.org/pdf/2606.15376): concurrency control with agent-judged repair.
- [Co-Coder (2026)](https://arxiv.org/html/2606.00953v1): cohesion-aware partitioning; code at [CoCoder](https://github.com/Flitternie/CoCoder).

**Starting points to inspect (not yet read in full)**

- [AIDev dataset card](https://huggingface.co/datasets/hao-li/AIDev) and [table documentation](https://huggingface.co/datasets/hao-li/AIDev/blob/main/data_table.md); newer [AIDev-7.6M](https://huggingface.co/datasets/hao-li/AIDev-7.6M).
- [AIDev paper](https://arxiv.org/pdf/2507.15003).
- [AgenticFlict (2026)](https://arxiv.org/abs/2604.03551): textual merge conflicts in agent PRs.
- [STALE: Passes Alone, Fails Together (2026)](https://arxiv.org/pdf/2609.25396): semantic-coordination benchmark.
