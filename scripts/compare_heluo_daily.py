"""Compare platform and H10b candidate intervals without changing either engine.

Run: python scripts/compare_heluo_daily.py --h10b-src /path/to/independent/src
     --output /tmp/heluo-daily.jsonl
The independent tree must be the separately reviewed 1925adf0 revision.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path


PROFILES = (
    ("beijing", "1980-06-22", 12, 30, "male", "CN_BEIJING", "Asia/Shanghai"),
    ("new_york", "1984-12-07", 16, 30, "female", "US_NEW_YORK", "America/New_York"),
    ("sydney", "1990-03-18", 8, 15, "male", "AU_SYDNEY", "Australia/Sydney"),
)
YEARS = (2024, 2026, 2027)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--h10b-src", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, help="Optional number of days per profile for a smoke test")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    h10b_root = Path(args.h10b_src).resolve().parent
    expected = '1925adf0e796e7346960c4cc2ed7f1af12449355'
    h10b_revision = subprocess.run(['git', '-C', str(h10b_root), 'rev-parse', 'HEAD'],
        check=True, capture_output=True, text=True).stdout.strip()
    if h10b_revision != expected:
        raise SystemExit(f'Independent revision {h10b_revision} differs from expected {expected}')
    platform_revision = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
        check=True, capture_output=True, text=True).stdout.strip()
    sys.path.insert(0, str(Path(args.h10b_src).resolve()))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from tongshu.engines.bazi_adapter import BaziAdapter
    from tongshu.engines.bazi_engine import BaziEngine
    from tongshu.engines.heluo.canonical import HeluoCanonical
    from tongshu.engines.heluo_adapter import sanyuan
    from tongshu.engines.time.resolver import TimeResolver
    from tongshu.pipeline_stages.compute_stage import ComputeStage
    from heluo_engine.adapter import HeluoAdapter
    from heluo_engine.engines.heluo.canonical import resolve_jieqi_window
    from heluo_engine.engines.heluo.timeline_yun import compute_liuri

    with open(args.output, "w", encoding="utf-8") as out:
        for label, dob, hour, minute, gender, location, timezone in PROFILES:
            ctx = TimeResolver().resolve_context(birth_date=date.fromisoformat(dob), hour=hour,
                minute=minute, gender=gender, timezone=timezone, location=location)
            chart = BaziAdapter(BaziEngine()).compute(ctx, gender=gender)
            pillars = ComputeStage._bazi_to_heluo_pillars(chart)
            birth = chart.birth_datetime
            platform = HeluoCanonical().calculate(bazi=pillars, gender=gender,
                birth_hour=pillars[3][1], era=sanyuan(birth.year), birth_year=birth.year,
                birth_date=birth.date().isoformat())
            segments = []
            for year in platform.timeline.yearly_hexagrams:
                for month in year.get("months", []):
                    for segment in month.get("days", []):
                        if segment.get("date_from") and segment.get("date_to"):
                            segments.append({"start": segment["date_from"], "end": segment["date_to"],
                                "hexagram": segment.get("name"), "yao_index": segment.get("flip_index"),
                                "jie": month.get("jie_datetime"), "year": year.get("year"),
                                "month": month.get("month")})
            independent = HeluoAdapter()
            interval_cache = {}
            emitted = 0
            for year in YEARS:
                day = date(year, 1, 1)
                while day.year == year:
                    if args.limit is not None and emitted >= args.limit:
                        break
                    iso = day.isoformat()
                    pm = [s for s in segments if s["start"] <= iso <= s["end"]]
                    window = resolve_jieqi_window(day.year, day.month, day.day)
                    h10b = []
                    error = None
                    actual = None
                    if not window.get("ok") or not window.get("jie_datetime") or not window.get("next_jie_datetime"):
                        error = "jie_unavailable"
                    else:
                        try:
                            result = independent.compute_from_chart(chart, target_date=iso)
                            actual = result.timeline.daily_hexagram
                            # A civil day can cross a jie boundary. Inspect both
                            # adjacent windows instead of silently selecting the
                            # window that the date-only adapter chose.
                            windows = {}
                            for delta in (-1, 0, 1):
                                sample = day + timedelta(days=delta)
                                win = resolve_jieqi_window(sample.year, sample.month, sample.day)
                                if not win.get('ok') or not win.get('jie_datetime') or not win.get('next_jie_datetime'):
                                    error = 'adjacent_jie_unavailable'
                                    break
                                windows[(day.year, win['jie_datetime'], win['next_jie_datetime'])] = win
                            start = datetime.combine(day, datetime.min.time())
                            end = start + timedelta(days=1)
                            for key, win in windows.items():
                                if key not in interval_cache:
                                    candidates = [m for y in result.timeline.yearly_hexagrams
                                        if y.get('year') == day.year for m in y.get('months', [])
                                        if m.get('month') == win['month']]
                                    if len(candidates) != 1:
                                        raise ValueError('independent_month_unavailable')
                                    month = candidates[0]
                                    interval_cache[key] = compute_liuri(month['lines'], month['yue_yao_index'],
                                        jie_datetime=win['jie_datetime'], next_jie_datetime=win['next_jie_datetime'],
                                        rule='hou5').days
                                for s in interval_cache[key]:
                                    a = datetime.fromisoformat(s['date_from'])
                                    b = datetime.fromisoformat(s['date_to'])
                                    if a < end and b > start:
                                        h10b.append({'start': s['date_from'], 'end': s['date_to'],
                                            'hexagram': s.get('name'), 'yao_index': s.get('flip_index'),
                                            'model_year': day.year})
                        except Exception as exc:
                            error = type(exc).__name__ + ": " + str(exc)
                    record = {"profile": label, "birth_date": dob, "birth_hour": hour,
                        "birth_minute": minute, "gender": gender, "birth_location": location,
                        "birth_timezone": timezone, "resolved_birth_datetime": birth.isoformat(),
                        "birth_pillars": pillars, "date": iso,
                        "platform_revision": platform_revision, "independent_revision": h10b_revision,
                        "platform": {"count": len(pm), "matches": pm,
                            "basis": "calendar-date inclusive; timeline_yun fixed 5-day segments"},
                        "h10b_candidate": {"count": len(h10b), "matches": h10b,
                            "basis": "hou5 candidate; half-open time intervals intersect civil date",
                            "timezone": "unknown: source timestamps are naive", "error": error},
                        "independent_production": {"count": None,
                            "status": "unknown_without_target_instant", "result": actual},
                        "jie_window": window}
                    out.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                    emitted += 1
                    day += timedelta(days=1)


if __name__ == "__main__":
    main()
