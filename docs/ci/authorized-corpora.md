# CI corpus boundaries

The public OS/Python matrix runs the repository tests with `-m "not authorized_corpus"`. Pytest reports the two non-public items as deselected. Neither item receives a passing result from the public suite. Running plain `python -m pytest` still requires both corpora and fails if either is missing.

| Corpus | Custody and source to record | Test |
| --- | --- | --- |
| Criteria | LIORIN rules custodian, authorized source snapshot with six original-text slices, generated anchor index and the source files used by that index | `tests/test_criteria_anchors.py` |
| Real cases | LIORIN case-data custodian, its approved original case export and export version | `tests/test_real_case_smoke.py` |

The owner of each corpus must confirm the permitted runner, read-only purpose and retained access before enabling the manual **Authorized corpus validation** workflow. Use a restricted runner group bound to this repository and workflow at `refs/heads/main`; the label alone is insufficient. The runner needs read-only sources mounted outside its checkout, a protected `liorin-authorized-ci` environment and approval from the designated custodian. Do not attach this job to PR or fork events. No corpus is committed or uploaded, and the job emits only per-test results. The owner provisions and controls the actual runner and manifests.

Set the protected environment variables `LIORIN_CRITERIA_ROOT`, `LIORIN_REAL_CASES_FILE`, and `LIORIN_CI_DATA_MANIFEST` to private paths. The manifest is JSON with `schema: 1`, `scope: "liorin-ci-read-only"` and `inputs.criteria` and `inputs.cases` records. Each record requires `owner`, `source`, `version`, `authorization` and the exact `sha256` file map returned by `tools.authorized_corpus_ci.inventory(name, location)`. The custodian prepares and reviews it outside the checkout using the authorized snapshot. Refresh the manifest only when accepting a new source version. Do not generate it automatically from the runner's mounted data at test time.

`python tools/authorized_corpus_ci.py` performs the same check locally on authorized inputs. Exit 2 means **UNVERIFIED** for missing or mismatched provenance. Exit 1 means one or both executed checks did not pass. Exit 0 means both ran and passed. An unprovisioned workflow or a missing run remains unverified.

Rollback by reverting the CI governance commit. The earlier complete-suite command will again require both corpora in every matrix job.
