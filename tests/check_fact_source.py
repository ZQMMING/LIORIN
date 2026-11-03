"""Required acceptance preflight: archived fact fallbacks cannot certify accuracy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    try:
        from engines.common.l0_fact_builder import _HIDDEN_GUARD
        from engines.l0_paipan import _chart_from_pillars
        if not _HIDDEN_GUARD.get('checked'):
            print('BLOCKED authoritative fact source:', _HIDDEN_GUARD.get('reason'))
            return 2
        chart = _chart_from_pillars({
            'year': ['癸', '亥'], 'month': ['壬', '戌'],
            'day': ['乙', '未'], 'hour': ['壬', '午'],
        })
        required = ('hidden_stems', 'stem_ten_gods', 'twelve_growth', 'kong_wang')
        if not all(key in chart for key in required):
            print('FAIL authoritative fact source contract incomplete')
            return 1
    except (ImportError, FileNotFoundError) as exc:
        print('BLOCKED authoritative fact dependency:', repr(exc))
        return 2
    except Exception as exc:
        print('FAIL authoritative fact source:', repr(exc))
        return 1
    print('PASS authoritative fact source available; no archived fallback')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
