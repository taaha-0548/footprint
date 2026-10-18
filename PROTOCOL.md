# PROTOCOL (human-owned)

Changes after results exist require human approval and a dated entry in the log below.

## Research questions
| ID | Question |
| --- | --- |
| RQ1 | File level: how accurately do deterministic methods predict the files a task changes, given only pre-work task text and the repo at the base commit? |
| RQ2 | Symbol level: the same for symbols written, and for the internal symbols the change depends on. |
| RQ3 | Misses: which categories are systematically missed (new files, tests, config, renames, dynamic references, files outside the import graph)? |
| RQ4 | Input text: how much do results change between title only, title plus linked issue, and PR body (a leaky upper bound)? |

## Metrics
- File level: precision@k and recall@k for k in {1, 3, 5, 10}; R-precision; MRR of the first correct file.
- Symbol level: the same for symbols written, plus recall of internal symbols read.
- Every metric per predictor and text variant, with 95% intervals from a bootstrap resampling repositories.
- Misses: share of missed ground-truth files by category (new file, test, config or docs, renamed, outside the import graph of the top predictions, non-Python).
- Coverage: PRs entering and leaving each stage, with reasons.

## Scope decisions (Checkpoint A, approved 2026-10-18)
- Dataset: `hao-li/AIDev` at tag `v4`; exact commit hash recorded in `configs/study.yaml` once resolved. Before M5, check whether v4 contains the Xu et al. PRs.
- PRs: merged only (primary analysis). Closed-unmerged deferred.
- Filters: Python repos, min_stars = 100, max_files_changed = 50. Post-extraction filter: at least one `.py` file changed (report count removed).
- All results are also reported by PR-size bucket (files changed): 1-2, 3-5, 6-15, 16-50.

## Decision rules
| Question | Rule | Threshold |
| --- | --- | --- |
| Is the ground truth trustworthy? | Human spot-check agreement on the 20-PR review sheet | >= 18/20 proceed; 15-17 fix and redo; < 15 stop |
| Does the extractor match GitHub? | Pilot file-list exact-match rate vs GitHub API file sets | >= 95% |
| Is prediction good enough to continue to Part 2? | Best deterministic predictor's file recall@5, primary variant | >= 0.60 viable; 0.30-0.60 partial; < 0.30 not viable |
| Does graph expansion help? | P4 minus P2 file recall@5 | >= 0.05 and 95% CI excludes 0 |
| How much does the PR body leak? | Title-plus-body recall@5 minus primary-variant recall@5 | substantial if >= 0.10 |

Primary variant: `title_issue` if >= 30% of dev PRs have a linked issue; otherwise `title` only, with `title_issue` as a subset analysis.

## Change log
| Date | Change | Reason | Approved by |
| --- | --- | --- | --- |
