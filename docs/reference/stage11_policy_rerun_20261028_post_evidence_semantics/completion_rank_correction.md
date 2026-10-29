# Correction notice — evidence completion ranks

An off-by-one error in the evaluator used for this historical snapshot reported `legacy_evidence_list_completion_rank` and its MRR one rank larger than the correct rank. The completion@k rate was unaffected. The retrieved chunks and all retrieval/routing and standard evidence precision/recall/nDCG metrics were unaffected.

This directory is preserved as an immutable historical snapshot. Use the corrected current reports in [`stage11_policy_rerun_20261028_post_image_policy_compositional/`](../stage11_policy_rerun_20261028_post_image_policy_compositional/) and their manifest. The current comparison confirms the 12 non-image reports retain their standard metrics.

| Report | Historical MRR (incorrect) | Corrected MRR | Completion@5 (both) |
|---|---:|---:|---:|
| `evidence_v3_viewed.json` | 0.308333 | 0.533333 | 0.800000 / 0.800000 |
| `expansion_dev.json` | 0.375000 | 0.668182 | 0.954545 / 0.954545 |
| `expansion_dev_concept_rerank.json` | 0.336364 | 0.598485 | 0.863636 / 0.863636 |
| `expansion_dev_strict.json` | 0.015152 | 0.022727 | 0.045455 / 0.045455 |
| `synovial_source_dev.json` | 0.333333 | 0.541667 | 1.000000 / 1.000000 |
| `synovial_source_dev_strict.json` | 0.000000 | 0.000000 | 0.000000 / 0.000000 |
| `synovial_synonym_dev.json` | 0.500000 | 1.000000 | 1.000000 / 1.000000 |
| `synovial_synonym_dev_strict.json` | 0.500000 | 1.000000 | 1.000000 / 1.000000 |
| `v2_test_concept_rerank.json` | 0.458333 | 0.875000 | 1.000000 / 1.000000 |
| `v2_test_regression.json` | 0.364583 | 0.691667 | 0.875000 / 0.875000 |
| `v2_test_strict.json` | 0.000000 | 0.000000 | 0.000000 / 0.000000 |

The corrected rank is the prefix length at which the final required legacy-listed chunk first appears. These flat lists still do not establish that every listed chunk is required evidence or that alternatives are interchangeable. No current dataset has reviewer-authored `evidence_groups`.
