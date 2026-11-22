# Product B status

Base `6f407f8997d4d78ce44504bc34b09d7c132612e7` verified against remote main. Development branch `codex/product-b-today`. The previous independent local QA service remains a separate sandbox.

## Round 9 merge review

- [#19](https://github.com/ZQMMING/LIORIN/pull/19) targets `main` and is ready for human review as an isolated preview. The route is absent from the default app. In isolated mode the product API validates a bearer session, loads the caller's saved profile by the authenticated user ID, normalizes the saved birth context, and invokes the packaged Bazi and Heluo adapters. Preview responses use `Cache-Control: no-store`. The regression uses two real test accounts: the owner gets the pending-review preview, the account without a profile gets 404, and a revoked owner session gets 401. The formal route returns 503.
- The #19 frontend workflow now builds Product B on PRs targeting `main` as well as building the default application. Locally, the preview build passed, 75 scoped API and engine tests passed, and four isolated account tests passed, including Chromium with the test PostgreSQL and SMTP sink. Approve the preview route, owner scoping, engine marker provenance and isolated test mode before merging. The formal route and null effective fields are outside that approval.
- [#21](https://github.com/ZQMMING/LIORIN/pull/21) targets `main` independently. Its [public run](https://github.com/ZQMMING/LIORIN/actions/runs/45027047847) passed four OS/Python matrix jobs, Ruff, and the wheel install and self-check. A local rerun passed 1,678 public tests and 5,071 subtests, with 10 existing skips and two private checks deselected. Review the subprocess collection and failure propagation, the explicit `heluo_engine` binding in `engines/l0_paipan.py`, and the [CI corpus boundaries](https://github.com/ZQMMING/LIORIN/blob/ceb005679ac5cfd1dcb93a6b48821c7227ccc0be/docs/ci/authorized-corpora.md). Criteria anchors and real-case smoke have no hosted passing result. The data custodian and repository administrator must approve the manifests, protected environment and isolated runner before the private workflow can run.
- Prefer merging #21 after human approval, then rerunning #19's full and scoped CI against the updated `main` before accepting #19. Recheck and retarget #20, #22 and #23 individually after each parent lands. If a parent is squash-merged, inspect the child diff for duplicate ancestor changes before retargeting. Default account and formal personal TODAY remain unavailable. Product B does not admit new Daily Explorer fields, effective INSIGHT dates, strength judgments, or production NFC authentication in this review.
- Revert the two Round 9 #19 commits in reverse order to remove the additional build and test coverage. Revert the #19 merge to remove the entire isolated preview. Reverting #21 restores the original CI collector and corpus requirements, including its known failures without the private inputs. No migration, Golden update or production configuration change is involved.

| User journey | Code and verification | Status |
| --- | --- | --- |
| NFC entry and claim | No device-claim flow located in the Product API or React entry. The old platform NFC routes were disabled. | Target chip and claim proof policy pending. |
| Sign in, save and recover profile | Existing `services/liorin_api/account` and React account screens. Real HTTPS Chromium against the allowed loopback PostgreSQL and SMTP sink. | Isolated testing. Production identity and schema pending. |
| TODAY | Saved profile → civil time normalization → packaged TimeResolver → BaziAdapter → HeluoAdapter → typed FastAPI response → React preview. | Real computation under test; product rule and copy admission pending. |
| Daily Explorer | The isolated TODAY preview can request previous and next civil dates through the same authenticated engine route. Browser regression covers recovery from an unavailable ordinal and leap-day navigation. | Calendar navigation available for preview. Direction, zodiac and traditional time-window sources still require field-level admission. |
| YOU, INSIGHT | No admitted content to these screens yet. | Evidence, contracts and tests required before release. |
| RELATION, ME, localization | Account screens are reused. Current English preview is partial coverage. | Consent, rights, recovery and complete en/zh-Hans/zh-Hant pending. |

## Calendar and time decision

The 2026-11-21 owner decision selects `gua6` for Product B. `hou5` stays available in the engine for comparison. The product preview does not consume the old five-day UI contract.

- `canonical.resolve_jieqi_window` assigns a requested civil date to a solar-term window by calendar date and counts the anchor's calendar date as ordinal 1. The engine obtains the anchor strings through sxtwl JD conversion and formats them to minute precision.
- `timeline_yun.compute_daily_base_hex` calculates the marker as the first anchor plus (ordinal − 1) × (next anchor − first anchor) / 30, then serializes to the minute. For the Beijing sample on 2026-08-17, the anchors are 2026-08-07 19:42 and 2026-09-07 22:40. Ordinal 11 gives 2026-08-18 04:41. The civil-date selection and the fractional interval calculation are distinct.
- The production anchor path is `resolve_jieqi_window → _compute_year_jie → jieqi_timeline → getJieQiByYear → JD2DD`. The day-scan fallback uses `getJieQiJD → JD2DD`. Both entry points in the [sxtwl 2.0.7 source distribution](https://pypi.org/project/sxtwl/2.0.7/#files) call `qi_accurate` (`src/eph.h`), which subtracts ΔT from the astronomical time and adds eight hours. Three production anchors match the dated API and the existing `jd_to_datetime` converter to the minute. The forecast clock is fixed UTC+08:00. The saved birth zone belongs to `CalculationContext`, while the requested civil date and the validated display zone are echoed independently.
- The preview retains the raw marker and returns its UTC equivalent at engine minute precision. It labels the Beijing marker `Asia/Shanghai` where the IANA zone agrees with the fixed clock and `+08:00` where historical Shanghai offsets differ. August 17's engine marker is `2026-08-18 04:41` in `Asia/Shanghai`, corresponding to `2026-08-17T20:41:00Z`. An unverified sxtwl version or pre-Gregorian anchor leaves the conversion null.
- In the shorter February 4–March 5 window (29 days, 17:57), March 4 is ordinal 29 and its marker falls on March 3 at 22:22. In the longer August 7–September 7 window (31 days, 02:58), September 5 is ordinal 30 and its marker falls on September 6 at 21:46. September 6 requests ordinal 31 and fails closed. September 7 selects ordinal 1 from the civil date, while that day's solar-term anchor is at 22:40. Day ordinals select engine rows. Fractional markers express positions along the solar-term span.
- **Formal TODAY review blocker:** the rule owner must approve how civil day ordinals map to actual effective time intervals and active lines, including the ordinal-31 case and handoff on the solar-term date. The engine-selected line remains diagnostic. With `admission_status=pending_review`, `active_yao_index`, `valid_from` and `valid_until` remain null and `/v1/personal/heluo-today` returns 503. The preview rejects `hou5` and missing or non-unique markers.

The live `TimeResolver → BaziAdapter` regression for Beijing on August 21–22, 2024 confirms 丁巳/辛亥 at true solar 22:59, 丁巳/壬子 at 23:00 and 23:59, and 戊午/壬子 at 00:00. Only explanatory comments and the misleading warning were corrected in the engine.

The original Hetu is displayed inside a slow CSS rotation wrapper with a pause control and reduced-motion support. Its SHA-256 is `7bafbd74888912371660965896c81aa9e32e9475db545ffd1444c7d439e0bd28`.

## Verification

| Command | Exit | Observed result |
| --- | --- | --- |
| `npm test` in frontend-case | 0 | 73 passed with default build settings. |
| `VITE_LIORIN_PRODUCT_B_PREVIEW=1 npm run build` in frontend-case | 0 | TypeScript and Vite verified. PowerShell users can set the flag via `$env:VITE_LIORIN_PRODUCT_B_PREVIEW='1'`. |
| `python -m pytest services/liorin_api/tests tests/heluo/test_h10b_jie_interval.py tests/heluo/test_heluo_lazy_liuri.py -q -p no:cacheprovider` | 0 | 75 passed. Includes late-zi pillars, short and long solar-term windows, leap day, cross-year, DST dates, UTC source parity, determinism, rule isolation and absent evidence. |
| `python -m pytest --collect-only -q -o addopts=''` | 3 | Existing `tests/test_ancient_case_golden.py:15` exits during collection. |
| `python -m pytest services/liorin_api/account_tests/test_account_browser.py -q -o addopts=''` | 0 | One real Chromium journey passed with the isolated PostgreSQL and SMTP fixture. Verified anonymous 401, saved profile, preview with UTC marker and provenance, ordinal-31 failure, session restore and logout. Captured 375px and 1440px results. |

To reproduce the real browser journey, build with the preview flag as above and run `python -m pytest services/liorin_api/account_tests/test_account_browser.py -q -o addopts=''` with that flag and the approved isolated test DSN and data directory. The test starts its own loopback HTTPS service and email sink. Optional `LIORIN_PREVIEW_SCREENSHOTS` writes 375px and 1440px captures of the synthetic case. The typed response is generated by FastAPI through `app.openapi()` when the isolated test account runtime is attached. No cloud database, real mail or migrations are needed for the targeted API CI.

Rollback uses a normal revert of this PR. Account data has no schema changes.
