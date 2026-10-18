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

## Decision rules (thresholds to be filled by the human at Checkpoint A)
| Question | Rule | Threshold |
| --- | --- | --- |
| Is the ground truth trustworthy? | Human spot-check agreement on the 20-PR review sheet | ___ of 20 |
| Does the extractor match GitHub? | Pilot file-list agreement with the GitHub API | ___ % |
| Is prediction good enough to continue to Part 2? | Best deterministic predictor's file recall@5, title-plus-issue variant | ___ |
| Does graph expansion help? | P4 minus P2 file recall@5, interval excluding zero | yes / no |
| How much does the PR body leak? | Title-plus-body recall@5 minus title-plus-issue recall@5 | ___ |

## Change log
| Date | Change | Reason | Approved by |
| --- | --- | --- | --- |
