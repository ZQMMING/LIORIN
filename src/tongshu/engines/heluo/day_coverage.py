"""Defensive inspection of existing platform day segments; no rule inference."""
from datetime import date, datetime


def inspect_day_coverage(result, target: date) -> dict:
    if result is None:
        return {'status': 'unavailable', 'reason': 'engine_unavailable', 'match_count': None}
    years = getattr(getattr(result, 'timeline', None), 'yearly_hexagrams', None)
    if not isinstance(years, list):
        return {'status': 'unknown', 'reason': 'timeline_unavailable', 'match_count': None}
    matches = []
    seen_year = False
    for year in years:
        if not isinstance(year, dict) or type(year.get('year')) is not int:
            return {'status': 'unknown', 'reason': 'invalid_timeline', 'match_count': None}
        if abs(year['year'] - target.year) > 1:
            continue
        seen_year = True
        months = year.get('months')
        if not isinstance(months, list):
            return {'status': 'unknown', 'reason': 'months_unavailable', 'match_count': None}
        for month in months:
            if not isinstance(month, dict) or not month.get('jie_datetime'):
                return {'status': 'unknown', 'reason': 'jie_unavailable', 'match_count': None}
            try:
                datetime.fromisoformat(month['jie_datetime'])
            except (TypeError, ValueError):
                return {'status': 'unknown', 'reason': 'jie_unavailable', 'match_count': None}
            segments = month.get('days')
            if not isinstance(segments, list) or not segments:
                return {'status': 'unknown', 'reason': 'segments_unavailable', 'match_count': None}
            for segment in segments:
                try:
                    start = date.fromisoformat(segment['date_from'])
                    end = date.fromisoformat(segment['date_to'])
                    if start > end:
                        raise ValueError('reversed interval')
                except (TypeError, ValueError, KeyError):
                    return {'status': 'unknown', 'reason': 'invalid_interval', 'match_count': None}
                if start <= target <= end:
                    matches.append(segment)
    if not seen_year:
        return {'status': 'unavailable', 'reason': 'year_unavailable', 'match_count': 0}
    count = len(matches)
    if count != 1:
        return {'status': 'unavailable', 'reason': 'missing' if count == 0 else 'ambiguous', 'match_count': count}
    segment = matches[0]
    lines = segment.get('lines')
    index = segment.get('flip_index')
    if (not segment.get('name') or not isinstance(lines, list) or len(lines) != 6
            or any(type(x) is not int or x not in (-1, 0, 1) for x in lines)
            or type(index) is not int or not 0 <= index < 6):
        return {'status': 'unknown', 'reason': 'invalid_segment', 'match_count': count}
    return {'status': 'ready', 'reason': None, 'match_count': count}
