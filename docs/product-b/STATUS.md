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
| Independent CI recovery | PR #21 (`ad7489cb`) collected 1,687 and ran 1,674 passing, 3 failing, 10 skipped and 5,071 passing subtests locally. The [remote matrix](https://github.com/ZQMMING/LIORIN/actions/runs/44899843263) completed test execution on all four targets with 1,648 passing, 5 failing and 21 skipped on each. The five failures are two consumers of the legacy `tongshu.facts` import, the stale bingyao integration input, the absent real-case fixture, and the machine-specific criteria-anchor workspace. Remote Ruff fell to 38, comprising 30 E712 and 8 C401. Full CI remains open. |
| Calendar branch targeted GitHub Actions | [API](https://github.com/ZQMMING/LIORIN/actions/runs/44900096761), [account](https://github.com/ZQMMING/LIORIN/actions/runs/44900096607) and [frontend](https://github.com/ZQMMING/LIORIN/actions/runs/44900096625) succeeded for `adbd98c4`. |

## Round 5

### Isolated credential incident

The confirmed exposure was a failure report from the local account browser run. The authorized loopback test database and role were verified against the approved data directory, then the role password was rotated and the existing restricted local credential source was updated. A new connection succeeded, the old password was explicitly rejected and no other role sessions were active during rotation. The product GitHub Actions jobs do not use the isolated DSN or a database secret, so no CI secret was added.

Six existing synthetic browser captures were visually checked. The scanned local logs and report files had no additional occurrence of the exposed value. The database log and new JUnit report contain neither the replacement value nor a SCRAM verifier. The reviewed API, account and frontend runs uploaded no artifacts. The mutation archive contained three entries, with no DSN or credential pattern detected. The existing tool report may still retain the revoked value.

Account pytest reports now redact known DSN, password, authorization token and mail-code values before terminal and JUnit rendering. An intentional synthetic failure and skip exercise both report paths. Credential rotation is independent of code rollback. Reverting code must not restore the revoked database password.

### Daily Explorer field review

| Field | Verified source, input, example and output | Product state |
| --- | --- | --- |
| Daily branch | Registered `lunar_python 1.4.8` day Gan-Zhi cross-checked with `sxtwl 2.0.7` and the same branch enumeration used by the Bazi package. The existing `HuangliEngine.get_day` agrees across February 17–28, 2026, covering all 12 branches. February 17 returns 戌. The input is the explicit Gregorian date. | Returned as a public calendar fact. A mismatch suppresses only the branch and keeps the lunar date. |
| Wealth direction | `HuangliEngine.get_day` → `getDayPositionCai` → `POSITION_CAI`, indexed by the day stem. 壬 returns 离. The output vocabulary is the eight direction trigrams. | Unavailable pending an approved rule citation and field-level verification. |
| Joy direction | `getDayPositionXi` → `POSITION_XI`, indexed by the day stem. 癸 returns 巽. Same vocabulary, distinct table. | Unavailable pending independent field admission. |
| Blessing direction | `getDayPositionFu` offers `POSITION_FU` and `POSITION_FU_2`. For 壬 the first returns 乾 and the default second returns 巽. | Unavailable pending selection and citation of the tradition. |
| Zodiac connections | `HuangliEngine` returns the public day clash branch. The birth-year animal differs between Lunar New Year and Li Chun on February 16, 2026. Date-only and instant-based Li Chun also differ before the term on February 4. | Day branch is visible. Personal zodiac, clashes and combinations require an approved year boundary and rules. No life outcome is inferred. |
| Traditional time windows | `lunar_python` `getTimes` yields 13 civil-day entries, including 子 segments at 00:00–00:59 and 23:00–23:59. The provider returns clock labels without assigning a user IANA timezone or resolving DST. | Unavailable pending local-time, midnight, DST and field-specific auspiciousness decisions. The display zone is echoed independently. |

### Review, CI and rollback

- Verified open stack: #19 → `main`, #20 → #19, #22 → #20. #19 remains the isolated preview review boundary. Formal Heluo TODAY stays 503 and the undetermined effective fields stay null. Retarget downstream PRs only after their upstream merges.
- #21 remains independent against `main`. Commit `ccd1591c` repoints the legacy birth-facts adapter at its renamed `heluo_engine` package and supplies the integration test's pillars as the production call does. Commits `bbc7fb0b` and `7fccb28c` resolve the original-text matrix and validator registry from the current checkout and write the generated test report only to a temporary directory. The old script rewrote a generated report in the reference workspace during an earlier run. Its current SHA-256 matches the tracked report. Ruff passes. Full local pytest passed with 1,677 tests, 10 existing skips and 5,071 passing subtests when supplied with `LIORIN_CRITERIA_ROOT` for the authorized source/slice workspace and `LIORIN_REAL_CASES_FILE` for the authorized case corpus. Public CI keeps both checks active and reports absent inputs as failures. Neither corpus is uploaded by these PRs.
- Round 5 local verification passed 84 API/Heluo tests, 76 frontend tests, the production build and three isolated PostgreSQL/SMTP tests including Chromium. The tests cover all 12 calendar branch codes, source disagreement, the synthetic pytest report and frontend recovery. Reproduce with the API/Heluo command above, `npm test`, the preview production build and `python -m pytest services/liorin_api/account_tests -q -o addopts=''` with approved local settings.
- Revert the corresponding PR commits for code rollback. Keep the rotated local role password in use.

## Round 6

### Merge checklist

| PR | Human review before merge | Dependency and follow-up |
| --- | --- | --- |
| #19 | Confirm private route exists only in the isolated account runtime, account identity selects the stored profile, preview responses use `no-store`, unresolved validity fields stay null, and real-browser evidence comes from PostgreSQL/SMTP capture. | Targets `main`. Merge acceptance only covers the isolated preview. Formal Heluo TODAY stays 503. |
| #20 | Confirm date navigation preserves the explicit date/zone and distinguishes leap day and ordinal-31 failure recovery. Check real requests and dedicated CI. | Targets #19. After upstream merge, inspect the remaining diff, retarget to `main` and rerun API, frontend and browser checks before review. |
| #22 | Confirm calendar and private results load independently, source versions are pinned, day branch fails closed on disagreement, pending fields stay unavailable, and test output redaction works. | Targets #20. Repeat diff, retarget and validation only after #20 merges. |
| #21 | Confirm public and authorized checks have distinct scope, validate the corpus custodian's approved runner group and manifest, and keep required private evidence visible. | Independent against `main`. Public matrix explicitly deselects two private tests. The manual private workflow requires external provisioning. |
| Personal DNA | Review narrow authenticated projection, absence of private birth inputs from the response, fixed fact provenance, missing-profile and DST-time responses, and English/simplified/traditional Chinese text. | Stacked on #22. After upstream integration, verify the remaining diff, build with Product B enabled, and rerun isolated browser/account checks. |

Daily Explorer retains the existing independent day-branch cross-check. Wealth and Joy still each need their own authoritative table citation and accepted examples. Blessing also needs approval of the tradition variant because the two tables disagree for 壬. Zodiac needs an approved Lunar New Year versus Li-Chun boundary, with exact term handling if selected, before producing a personal animal or relationship. Traditional hours need a declared local-time basis, a 子-hour handoff and a DST gap/fold policy before publishing effective time intervals or auspiciousness. These statuses do not change the approved `gua6` clock and admission contract.

### Personal DNA and device foundation

- `GET /v1/personal/dna` exists only in the isolated account runtime. It shares the existing birth-chart adapter path with the Heluo preview. The API returns the birth-year Na Yin, day master and each pillar's stem/branch element with package and calculation versions. Absent profile returns 404, missing minutes or ambiguous/nonexistent local time return 422. Zodiac remains pending. The projection contains no hidden-stem scores, preference judgments or Ziwei interpretations.
- Product B uses the existing shell with Today, You, Insight, Relation and Me. `/you` has English, Simplified Chinese and Traditional Chinese copy, with a link to the birth profile when needed. Insight and Relation display availability honestly. Product A navigation and original Hetu remain intact.
- The isolated device lifecycle proves registration, account-bound one-time signed claims, re-touch, expiry, loss and revocation using a generated test signing key. It registers no public route and issues no account credential. Physical proof format, approved hardware key provisioning, durable ownership and lost-device/account recovery require the designated security and product owners.
- Local results were 89 backend/Heluo tests, 78 frontend tests, production-mode build, changed-file Ruff and four isolated account/device tests. Chromium exercised the real sign-in, saved profile, YOU, language selector and reload restoration. A second account received 404 on DNA while the first account had a stored profile.
- #21 at `ceb00567`: local public scope passed 1,678 tests, with 10 existing skips and two marked tests deselected. Both private tests passed locally under a manifest bound to the authorized data fingerprints. GitHub's protected environment and runner are still unprovisioned, so no remote private pass is claimed. The public workflow reports the restricted scope.

For rollback, revert the Personal DNA branch commits and rebuild with the previous Product B bundle. Reverting the independent CI governance commit restores the prior all-corpus matrix behavior. Neither rollback requires database changes.

## Round 7

### Integration checks

| PR | Required evidence before human approval | After the upstream merge |
| --- | --- | --- |
| #19 | Confirm private route registration, owner-profile lookup, no-store responses, real isolated account/browser tests and null effective-period fields. Roll back by reverting the preview commits. | Formal `/v1/personal/heluo-today` remains 503. Keep the 31st day and effective interval under rule-owner review. |
| #20 | Verify date, leap-day and failure recovery in Chromium on the real API. Compare the five-file feature diff and rollback scope. | Retarget from #19 to `main`, inspect remaining changes and rerun frontend/API/browser tests. |
| #22 | Verify registered calendar sources, authenticated data separation, fail-closed day branch and credential report redaction. Preserve the rotated password during rollback. | Retarget only after #20; rerun product checks. Keep each unadmitted field unavailable. |
| #23 | Verify YOU honors authorization, incomplete and ambiguous birth time, and none of the pending results leak into the response. Review existing isolated NFC proof, app switch and rollback. | Retarget only after #22; rerun actual birth profile tests in Chromium. |
| #21 | Independently verify public matrix scope, no false claim of private verification, and a separately approved corpus runner/manifest. | Public matrix, Ruff and package self-check passed. The two private datasets passed locally; remote authorized execution still requires the protected runner. |

No merge or retarget was performed. The YOU/INSIGHT follow-up updates #23 itself. Its review history and #22 base remain in place.

### YOU and INSIGHT

- YOU displays a day-master identity, the traditional designation of the birth-year stem/branch, and counts of four stems and four branches. The five rows describe exactly eight positions. The source drawer records `E-SMTH-003-001` (the `NAYIN_60` table's reference to *San Ming Tong Hui*) and the live engine versions. Zodiac, useful elements, personality and Ziwei have separate pending statuses. The API exposes no preferred-element recommendation.
- `GET /v1/personal/insight?year=YYYY` is behind the isolated account runtime. It projects the existing Heluo annual cycle and twelve solar-term month hexagrams from the saved chart via `HeluoAdapter.compute_from_chart`. July 1 is an explicit calculation reference inside the requested year. The API does not treat it as the effective date for any cycle. The UI labels solar-term month ordinals and exposes the engine source. Ziping decade intervals and personal interpretation remain pending. The sample Beijing profile in API tests returned 丙午 / 天水讼 for 2026 and twelve month records.
- The public Daily Explorer calendar still verifies the day branch. The separate Wealth and Joy rules need individual authoritative citations and test cases. Blessing also needs a decision between the conflicting tables. Personal zodiac needs a year-boundary decision. Traditional hours need local-time, DST and midnight/子-hour interval admission.

### Device architecture boundary

No approved chip SKU, provisioning agreement or production key reference is in the handoff. The [NXP NTAG 424 DNA datasheet](https://www.nxp.com/docs/en/data-sheet/NT4H2421Gx.pdf) establishes AES-128 / SUN for that specific candidate. The Ed25519 prototype continues to verify isolated signed challenges only. A generated-key concurrency test confirms that two valid claims can bind only one account and the competing account cannot re-touch or mark the device lost.

The proposed persistent boundary is a server-managed device registry with SKU/protocol and a KMS key reference. Keep account authorization and device proof as separate inputs. A single database transaction must consume the proof/counter and confirm unique active ownership. Re-touch checks ownership through the current account session. Unlink requires recent account authentication; revocation retains a device tombstone and invalidates outstanding proofs. Lost-device recovery and account recovery require distinct approved proofs, an auditable rebind and invalidation of the old device or sessions. Production routes, key access, migrations and recovery stay gated until the chip, provisioning and recovery policy are approved.

Rollback by ordinary revert of the round 7 commits in #23. API changes are read-only. The original SVG and frozen engines remain at their round 6 versions.

Local verification passed 90 focused Python tests, 79 frontend tests, TypeScript/Vite production build, changed-file Ruff, and five isolated account/browser/device tests. Chromium covered saved-profile YOU, the table at 320px and 1440px, language switching, reload, Insight year selection, twelve result rows and both calculation source disclosures. The public CI fixes remain independent in #21.

## Round 8 integration review

Remote `main` is `6f407f89`. GitHub had no submitted reviews on #19–#23 when checked. The round 8 changes update #23 on its existing #22 base. The combined validation uses a detached local checkout with both the stacked product changes and independent CI recovery. GitHub branches, target branches and review states are unchanged.

| PR | Scope ready for human review | Gate before merge or retarget |
| --- | --- | --- |
| #19 (`e256aaa5`) | Authenticated isolated personal Heluo preview, shared birth chart, `gua6`, source and clock evidence. API, account and frontend checks passed for that head. | Review the isolated runtime, owner-only profile lookup, `no-store`, and raw engine marker contract. Formal route remains 503 and effective fields remain null. Legacy full CI still fails on this branch. |
| #20 (`516f13cb`) | Real adjacent-date navigation, leap day and ordinal-31 recovery. Frontend and account checks passed. | After #19 is accepted, compare remaining diff, retarget to `main`, then rerun dedicated API/frontend checks and real Chromium. |
| #22 (`f3ae938f`) | Verified lunar date and day branch, localized pending states and isolated test-report redaction. API, frontend and account checks passed. | After #20 lands, recheck real calendar source/version, controller lifecycle and redaction. Keep the rotated test password on rollback. |
| #23 | Integrated product review from saved birth profile through YOU, INSIGHT, TODAY, Daily Explorer and ME. | After #22 lands, inspect the remaining diff and rerun the isolated journey. Personal zodiac, useful elements, interpretation, Ziping effective periods and unsupported daily fields remain out of scope. |
| #21 (`ceb00567`) | Independent public CI recovery. Four OS/Python jobs, Ruff and package checks passed. | Review the two explicitly deselected corpus checks and data custody configuration. Both checks passed in local authorized testing. Remote protected runner remains unprovisioned. |

### Product journey

The Product B language selector controls navigation, account, YOU, INSIGHT, TODAY and Daily Explorer. It persists across reload in the same tab. Engine facts, canonical city IDs and source versions remain the same when language changes. Product B ME keeps email authentication. Device pairing requires the future device security integration.

YOU labels the eight counts as chart positions. INSIGHT identifies the calculation reference date as record selection and marks effective dates pending. The approved `gua6` boundary and fixed UTC+08:00 engine clock are unchanged. Day 31 can still show the public calendar even when the private preview is unavailable.

### Hardware verification preparation

NTAG 424 DNA remains a candidate. NXP's [data sheet, sections 8.2.3.4 and 9.3](https://www.nxp.com/docs/en/data-sheet/NT4H2421Gx.pdf) and [application note AN12196](https://www.nxp.com/docs/en/application-note/AN12196.pdf) document AES-128 Secure Dynamic Messaging / SUN. The device supplies a MAC and authenticated counter data when correctly provisioned. The counter is a 24-bit value tied to the enabled file. Certain repeated reads can return the same counter, and re-enabling SDM can reset it. Backend acceptance therefore needs a durable highest accepted counter per device and provisioning epoch. Chip input and hardware authenticity remain unverified until the physical SKU and sample vectors are approved.

Pending design review: bind each serial to the provisioned file profile and its versioned key handles. Separate provisioning administration, metadata access and MAC validation. A server verifier uses the registered profile to validate the message and counter before storing a proof outcome. Account authorization is an independent check. Claim or re-touch accepts a strictly newer counter and persists it in the same transaction as the ownership operation. Recovery consumes an independently authorized, one-time grant scoped to the account and both devices. Revocation leaves a tombstone and retires the old epoch. Production keys, chip configuration and deployment remain pending.

Disposable SQLite tests exercise the proposed transaction invariants with synthetic already-verified inputs. They cover concurrent claims, counter replay across reconnect, owner and epoch checks, rollback of an invalid recovery, single-use recovery and revocation of the lost device. The Ed25519 harness remains an independent isolated proof test. The SQLite tests exercise storage semantics. Physical SUN validation, production schema and account recovery policy require owner approval.

### Verification

- Round 8 Chromium used the approved isolated PostgreSQL and SMTP sink. It ran one continuous login → birth profile → YOU → INSIGHT → TODAY → Daily Explorer → ME → sign-out path. It checked that the signed-in session restores on reload, the signed-out session restore returns 401, and a subsequent YOU deep link displays only the sign-in prompt.
- The same browser case verifies three locales, stable birth timezone and Bazi calculation version across private routes, the reference-date label and pending effective dates, formal Heluo 503, ordinal-31 recovery, leap day, and pause/reduced-motion behavior. It checks horizontal overflow at 320px, 375px and 1440px on YOU, INSIGHT, TODAY and ME.
- Local results: 90 API/Heluo tests, 79 frontend tests, production build, seven isolated account/device tests including Chromium, and targeted Ruff. The isolated NFC transaction tests use a disposable SQLite file.
- Detached integration checkout `7a34c9e4` had no merge conflicts with #21 and passed the public scope with 1,678 tests, 10 existing skips, two private tests deselected and 5,071 passing subtests. The 77 API service tests and Ruff also passed in that checkout. Browser assertions were further strengthened and rerun in the product worktree. No remote merge state was changed.
- The final INSIGHT layout keeps the solar month markers inside their columns so two-digit month labels remain readable at 320px.

Round 8 rollback uses a normal revert of its commits in #23. The code changes do not migrate a database, change the original Hetu, or edit frozen algorithms or Golden assets.
