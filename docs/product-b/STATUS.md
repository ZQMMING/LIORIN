# Product B status

Base `6f407f8997d4d78ce44504bc34b09d7c132612e7` verified against remote main. Development branch `codex/product-b-today`. The previous independent local QA service remains a separate sandbox.

| User journey | Code and verification | Status |
| --- | --- | --- |
| NFC entry and claim | No device-claim flow located in the Product API or React entry. The old platform NFC routes were disabled. | Target chip and claim proof policy pending. |
| Sign in, save and recover profile | Existing `services/liorin_api/account` and React account screens. Real HTTPS Chromium against the allowed loopback PostgreSQL and SMTP sink. | Isolated testing. Production identity and schema pending. |
| TODAY | Saved profile → civil time normalization → packaged TimeResolver → BaziAdapter → HeluoAdapter → typed FastAPI response → React preview. | Real computation under test; product rule and copy admission pending. |
| Daily Explorer | The isolated TODAY preview navigates real adjacent civil dates and separately reads lunar month/day through FastAPI, the packaged `annotate_day` bridge and the registered `lunar_python 1.4.8` source. The calendar panel supports en, zh-Hans and zh-Hant. | The lunar date still renders when Heluo has no day ordinal. Directions, zodiac relations and traditional time windows remain unavailable pending field admission. |
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

## Round 4 review and calendar slice

- PR #19 (`e256aaa5`) is open for human review against `main`. The isolated runtime verifies the loopback database identity, requires local SMTP capture and HTTPS configuration, and authorizes preview requests using the saved account. The normal app has no private preview route. The formal route still returns 503. PR #20 (`516f13cb`) remains based on PR #19 until that review lands.
- `GET /v1/explorer/calendar` returns the reviewed calendar annotation for an explicit Gregorian date and echoes the validated display timezone. It reads no birth profile. The registered source version and existing bridge are checked before returning data. The product service pins the registered version 1.4.8 after the initial Linux CI pulled 1.4.9 and correctly received 503. Missing or incompatible source data returns 503. Dates before the source's Gregorian cutover are rejected. The browser fetches calendar and private Heluo independently.
- `HuangliEngine.get_day` exposes the three direction tokens and the day clash branch. Their presence in `data/calendar_sources.json` establishes provenance. The registry does not establish compass rule admission, a user-zodiac year boundary and relation policy, or the local/DST boundary policy and judgments for twelve traditional time windows. The response carries explicit unavailable states for these three sections.
- The Chromium run uses isolated PostgreSQL and captured SMTP. It verifies the real login/profile flow, that a synthetic tag/UID cannot authorize account reads, calendar source display, the ordinal-31 recovery and leap day. NFC ownership proof and production account credentials/schema remain outside the enabled runtime.

| Verification scope | Result |
| --- | --- |
| Calendar branch API and Heluo regression suite | 81 passed, including rejection of an unreviewed source version. |
| Calendar branch frontend and production-mode build | 75 passed, TypeScript/Vite build passed. |
| Chromium against isolated DB and SMTP | One complete journey passed. |
| Full CI before recovery | PR #19 Actions run `44897796954` aborted pytest with import-time `SystemExit` and Ruff found 281 violations. Both reproduced on `main@6f407f89`. |
| Independent CI recovery | PR #21 (`ad7489cb`) collected 1,687 and ran 1,674 passing, 3 failing, 10 skipped and 5,071 passing subtests locally. Remaining failures are the legacy `tongshu.facts` import, stale bingyao integration-relay input and an unavailable machine-specific real-case file. Ruff fell to 38, comprising 30 E712 and 8 C401. Full CI remains open. |
