# -*- coding: utf-8 -*-
"""H10b 移植：流日卦按节气实际间隔均匀分配（不再机械固定每段 5 日）。

原典依据（用户 2026-10-21 核证）：段边界按当月节时刻 T0 与下月节时刻 T1 的
实际间隔（节→节，约 29~31 日不等，含时刻）均匀切分，每段 = (T1-T0)/N。

同时引入 rule="gua6"（汉易「一爻一日、一卦六日」模型，5 段）。

改动：
  timeline_yun.compute_liuri  加 next_jie_datetime / rule 形参 + 均匀切分
  canonical._jie_interval_for_lunar_month  新增（包装已有的 _jie_datetime_for_lunar_month）
  canonical 调用处             传 next_jie_datetime
"""
from __future__ import annotations

import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TL = os.path.join(ROOT, "src", "tongshu", "engines", "heluo", "timeline_yun.py")
CN = os.path.join(ROOT, "src", "tongshu", "engines", "heluo", "canonical.py")


def read(p):
    with io.open(p, "r", encoding="utf-8", newline="") as fh:
        raw = fh.read()
    return raw.replace("\r\n", "\n"), ("\r\n" in raw)


def write(p, s, crlf):
    with io.open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s.replace("\n", "\r\n") if crlf else s)


def main():
    # ---------- timeline_yun.py ----------
    s, crlf = read(TL)
    if "next_jie_datetime" not in s:
        s = s.replace(
            "    jie_datetime: str | None = None,\n"
            "    align_dates: bool = False,\n"
            ") -> LiuRiResult:",
            "    jie_datetime: str | None = None,\n"
            "    next_jie_datetime: str | None = None,\n"
            "    align_dates: bool = False,\n"
            '    rule: str = "hou5",\n'
            ") -> LiuRiResult:",
            1,
        )
        # 段数：hou5=6 段（每爻管约 5 日）/ gua6=5 段（每卦管约 6 日）
        s = s.replace(
            "    base = _parse_datetime(jie_datetime) if (jie_datetime and align_dates) else None\n"
            "    days = []\n"
            "    for k in range(6):\n",
            "    n_seg = 6 if rule == \"hou5\" else 5\n"
            "    seg_len = 5 if rule == \"hou5\" else 6\n"
            "    base = _parse_datetime(jie_datetime) if (jie_datetime and align_dates) else None\n"
            "    nxt = _parse_datetime(next_jie_datetime) if (next_jie_datetime and align_dates) else None\n"
            "    days = []\n"
            "    for k in range(n_seg):\n",
            1,
        )
        # 段内天数切片
        s = s.replace(
            "        seg_days = positions[k * 5:k * 5 + 5]\n"
            "        flip_idx = seg_days[0]          # 段首爻位（保留旧键语义=该段第一日）\n"
            "        seg_lines = day_lines[k * 5][1]\n",
            "        seg_days = positions[k * seg_len:k * seg_len + seg_len]\n"
            "        flip_idx = seg_days[0]          # 段首爻位（保留旧键语义=该段第一日）\n"
            "        seg_lines = day_lines[k * seg_len][1]\n",
            1,
        )
        s = s.replace(
            "            dl = day_lines[k * 5 + j][1]\n",
            "            dl = day_lines[k * seg_len + j][1]\n",
            1,
        )
        s = s.replace(
            '                "day": k * 5 + j + 1,\n'
            '                "polarity": "阳日" if (k * 5 + j) % 2 == 0 else "阴日",\n',
            '                "day": k * seg_len + j + 1,\n'
            '                "polarity": "阳日" if (k * seg_len + j) % 2 == 0 else "阴日",\n',
            1,
        )
        s = s.replace(
            '                    item["date"] = (base + timedelta(days=k * 5 + j)).strftime("%Y-%m-%d")\n',
            '                    item["date"] = (base + timedelta(days=k * seg_len + j)).strftime("%Y-%m-%d")\n',
            1,
        )
        s = s.replace(
            '            "segment": k + 1, "day_from": k * 5 + 1, "day_to": k * 5 + 5,\n',
            '            "segment": k + 1, "day_from": k * seg_len + 1, "day_to": k * seg_len + seg_len,\n',
            1,
        )
        # 节气对齐块 → H10b 均匀分配
        old_align = (
            '        if base is not None:\n'
            '            # 节气对齐：段k覆盖节起第(k*5+1)~第(k*5+5)天\n'
        )
        new_align = (
            '        if base is not None and nxt is not None and nxt > base:\n'
            '            # H10b 节气为界均匀分配：段边界 = 节时刻 + k*(下节-节)/N，\n'
            '            # 按实际节气间隔（含时刻）切分，不机械固定每段日数\n'
            '            try:\n'
            '                from datetime import timedelta\n'
            '                span = (nxt - base).total_seconds()\n'
            '                seg_sec = span / n_seg\n'
            '                b0 = base + timedelta(seconds=k * seg_sec)\n'
            '                b1 = base + timedelta(seconds=(k + 1) * seg_sec)\n'
            '                entry["day_from"] = int((b0.date() - base.date()).days) + 1\n'
            '                entry["day_to"] = int((b1.date() - base.date()).days)\n'
            '                if k == n_seg - 1:\n'
            '                    entry["day_to"] = int((nxt.date() - base.date()).days) + 1  # 末段至下一节\n'
            '                entry["date_from"] = b0.strftime("%Y-%m-%d %H:%M")\n'
            '                entry["date_to"] = b1.strftime("%Y-%m-%d %H:%M")\n'
            '                entry["jie_span_days"] = round(span / 86400.0, 4)  # 实际节气间隔（天）\n'
            '            except Exception as exc:\n'
            '                entry["jie_align_error"] = f"节气均匀分配失败：{exc}"\n'
            '        elif base is not None:\n'
            '            # 节气对齐：段k覆盖节起第(k*5+1)~第(k*5+5)天\n'
        )
        if old_align in s:
            s = s.replace(old_align, new_align, 1)
            print("  OK timeline_yun 均匀分配块")
        else:
            print("  FAIL timeline_yun 对齐块锚点未找到")
            sys.exit(1)
        write(TL, s, crlf)
        print("  OK timeline_yun.compute_liuri 签名+分段")

    # ---------- canonical.py ----------
    s, crlf = read(CN)
    if "_jie_interval_for_lunar_month" not in s:
        anchor = "def _jie_datetime_for_lunar_month(year: int, lunar_month: int) -> str | None:"
        idx = s.find(anchor)
        if idx < 0:
            print("  FAIL canonical 锚点未找到")
            sys.exit(1)
        block = (
            'def _jie_interval_for_lunar_month(year: int, lunar_month: int) -> tuple[str | None, str | None]:\n'
            '    """(当月节时刻, 下月节时刻) — 节气为界（H10b 规则分疏）。\n'
            '\n'
            '    流日卦段边界须按"节→下节"实际间隔（约 29~31 日不等）均匀切分，\n'
            '    不可机械固定每段日数。下月节跨年：亥月（12）→ 下一年链子月（大雪）。\n'
            '    """\n'
            '    t0 = _jie_datetime_for_lunar_month(year, lunar_month)\n'
            '    if t0 is None:\n'
            '        return None, None\n'
            '    nxt_lm = lunar_month + 1\n'
            '    nxt_year = year\n'
            '    if nxt_lm > 12:\n'
            '        nxt_lm = 1\n'
            '        nxt_year = year + 1\n'
            '    t1 = _jie_datetime_for_lunar_month(nxt_year, nxt_lm)\n'
            '    return t0, t1\n'
            '\n'
            '\n'
        )
        s = s[:idx] + block + s[idx:]
        print("  OK canonical._jie_interval_for_lunar_month")
        write(CN, s, crlf)

    # 调用处传 next_jie_datetime
    s, crlf = read(CN)
    if "next_jie_datetime=" not in s:
        old = '    jie_dt = _jie_datetime_for_lunar_month(y.year, m["month"])\n'
        new = (
            '    jie_dt = _jie_datetime_for_lunar_month(y.year, m["month"])\n'
            '    _jie_dt_next = None\n'
            '    try:\n'
            '        _jie_dt_next = _jie_interval_for_lunar_month(y.year, m["month"])[1]\n'
            '    except Exception:\n'
            '        _jie_dt_next = None\n'
        )
        if old in s:
            s = s.replace(old, new, 1)
            print("  OK canonical 调用处取下节时刻")
        else:
            print("  WARN canonical 调用处锚点未找到")
        write(CN, s, crlf)
    print("  done")


if __name__ == "__main__":
    main()
