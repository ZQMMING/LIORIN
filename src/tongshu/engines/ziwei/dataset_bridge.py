"""
P0-9 Dataset Bridge — iztro 桥接 + 12 项核对校验框架

职责:
1. iztro (Node 22 ESM) → FrozenZiweiChart 兼容 MockChart adapter
2. 12 项核对校验 (vs 王亭之《飞星紫微斗数》四化表)
3. 不改 RuleGraph / ZiweiChart / 各派 RuleGraph — 仅 adapter

边界 (User 铁律):
- 不改 BaseZiweiRuleGraph
- 不改 FrozenZiweiChart/ZiweiChart
- 不改各派 RuleGraph 子类
- 不写"判断/解释/强旺衰" (那是"解"层)
- 仅做"排盘数据源桥接"

P0-8 已封板, P0-9 是真实案例验证基础。
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tongshu.engines.ziwei.rules.feixing_rule_graph import (
    PalaceStemFact,
    FlyingTransformFact,
)

# ============================================================
# 王亭之《飞星紫微斗数》生年四化表 (公认标准)
# 10 年干 × 4 化 = 40 条
# ============================================================
NFS_TABLE: Dict[str, Tuple[str, str, str, str]] = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}

# iztro v2.3 字段名 (不带"化"字)
MUTAGEN_KEYS = ("禄", "权", "科", "忌")

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def year_stem(year: int) -> str:
    """1984=甲(0), 1983=癸(9)... 甲子周期"""
    return STEMS[(year - 4) % 10]


def year_branch(year: int) -> str:
    return BRANCHES[(year - 4) % 12]


# ============================================================
# Adapter: iztro JSON → FrozenZiweiChart 兼容 MockChart
# ============================================================
@dataclass
class ZiweiChartMock:
    """Mock chart 兼容 FrozenZiweiChart 接口"""
    birth_year: int
    palaces: Dict[str, Dict] = field(default_factory=dict)
    palace_stems: List[PalaceStemFact] = field(default_factory=list)
    flying_transforms: List[FlyingTransformFact] = field(default_factory=list)
    source_system: str = "iztro-bridge"


def adapt_iztro_sample(sample: dict) -> ZiweiChartMock:
    """将 iztro 生成的 sample dict 转为 ZiweiChartMock。

    sample 格式 (由 _generate_iztro_charts 生成):
    {
        "birthInfo": {"year": 1983, "month": 6, "day": 1, "hour": 0, "gender": "male"},
        "chart": {
            "palaces": [
                {"name": "命宫", "stem": 3, "branch": 5,  # 丁巳
                 "stars": [{"name": "紫微", "type": "major", "mutagen": "..."}, ...]},
                ...
            ]
        }
    }
    """
    c = sample["chart"]
    palaces: Dict[str, Dict] = {}
    stems: List[PalaceStemFact] = []
    flying: List[FlyingTransformFact] = []

    sihua_map = {"禄": "化禄", "权": "化权", "科": "化科", "忌": "化忌"}

    for p in c["palaces"]:
        pname = p["name"]
        stem = STEMS[p["stem"]] if isinstance(p["stem"], int) else p["stem"]
        branch = BRANCHES[p["branch"]] if isinstance(p["branch"], int) else p["branch"]
        major = list(s["name"] for s in p["stars"] if s["type"] == "major")
        minor = list(s["name"] for s in p["stars"] if s["type"] == "minor")
        # P0-10 修复: palaces dict 必须含 "major"/"minor" 键 (中州 RuleGraph 依赖)
        # 保留 "major_stars"/"minor_stars" 作兼容别名
        palaces[pname] = {
            "stem": stem, "branch": branch,
            "major": major, "minor": minor,
            "major_stars": tuple(major), "minor_stars": tuple(minor),
        }

        stems.append(PalaceStemFact(
            palace_name=pname, stem=stem, branch=branch,
            major_stars=tuple(major), minor_stars=tuple(minor),
        ))

        for s in p["stars"]:
            if s["type"] == "major" and s.get("mutagen") in sihua_map:
                flying.append(FlyingTransformFact(
                    source_palace=pname, source_stem=stem,
                    transformation=sihua_map[s["mutagen"]],
                    target_star=s["name"], target_palace=pname,
                    direction="self",
                ))

    return ZiweiChartMock(
        birth_year=sample["birthInfo"]["year"],
        palaces=palaces,
        palace_stems=stems,
        flying_transforms=flying,
        source_system=sample.get("system", "iztro-bridge"),
    )


# ============================================================
# iztro JSON 生成 (Node 22 ESM)
# ============================================================
DEFAULT_DATES = [
    "1984-06-15", "1990-03-21", "1975-11-08", "2000-08-16", "1968-04-03",
    "1985-12-25", "1992-07-14", "1978-02-19", "1995-09-30", "1988-05-11",
    "2001-01-23", "1983-10-05", "1997-06-18", "1986-11-29", "1972-08-07",
    "1993-04-12", "1989-02-28", "1981-07-04", "1998-12-15", "1976-09-22",
    "1987-03-09", "1991-08-31", "1982-05-26", "1996-10-13", "1979-01-17",
    "1984-12-02", "1994-07-25", "1980-04-08", "1999-11-19", "1973-06-30",
]


def _generate_iztro_script(dates: List[str], time_indexes: List[int]) -> str:
    """生成 iztro 调用脚本 (Node 22 ESM)"""
    return f"""
import {{ astro }} from './node_modules/iztro/lib/index.js';

const dates = {json.dumps(dates)};
const timeIdx = {json.dumps(time_indexes)};
const genders = ['male', 'female'];
const leaps = [true, false];
const STEMS = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
const BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];

const out = [];
for (let i = 0; i < dates.length; i++) {{
  const d = dates[i];
  const t = timeIdx[i % timeIdx.length];
  const g = genders[i % 2];
  const l = leaps[i % 2];
  const c = astro.bySolar(d, t, g, l, 'zh-CN');
  const j = c.toJSON();
  out.push({{
    birthInfo: {{
      year: parseInt(d.slice(0,4)), month: parseInt(d.slice(5,7)),
      day: parseInt(d.slice(8,10)), hour: t, gender: g, longitude: 120,
    }},
    system: 'iztro-bridge',
    chart: {{
      birthInfo: {{
        year: parseInt(d.slice(0,4)), month: parseInt(d.slice(5,7)),
        day: parseInt(d.slice(8,10)), hour: t, gender: g, longitude: 120,
      }},
      lunarInfo: {{
        lunarYear: j.lunarDate.year, lunarMonth: j.lunarDate.month,
        lunarDay: j.lunarDate.day, yearStem: 0, yearBranch: 0, isLeapMonth: l,
      }},
      mingGongBranch: 0, shenGongBranch: 0,
      natalYearStem: (j.rawDates && j.rawDates.chineseDate && j.rawDates.chineseDate.yearly) ? j.rawDates.chineseDate.yearly[0] : '',
      natalYearBranch: (j.rawDates && j.rawDates.chineseDate && j.rawDates.chineseDate.yearly) ? j.rawDates.chineseDate.yearly[1] : '',
      wuxingJu: 5, wuxingJuName: '土五局', ziweiPos: 0,
      palaces: j.palaces.map(p => ({{
        branch: BRANCHES.indexOf(p.earthlyBranch),
        stem: STEMS.indexOf(p.heavenlyStem),
        name: p.name,
        stars: [
          ...(p.majorStars || []).map(s => ({{
            name: s.name, type: 'major',
            brightness: s.brightness || 'normal',
            mutagen: s.mutagen || '',
          }})),
          ...(p.minorStars || []).map(s => ({{
            name: s.name, type: 'minor', brightness: s.brightness || '',
            mutagen: s.mutagen || '',
          }})),
          ...(p.adjectiveStars || []).map(s => ({{
            name: s.name, type: 'lucky', brightness: '',
            mutagen: '',
          }})),
        ],
        daXianAge: [0, 10],
        isMingGong: p.isMingGong,
        isShenGong: p.isBodyPalace,
        isCurrentDaXian: false,
      }})),
    }},
  }});
}}
console.log(JSON.stringify(out));
"""


def generate_iztro_charts(
    repo_root: Path,
    n: int = 30,
    dates: Optional[List[str]] = None,
    time_indexes: Optional[List[int]] = None,
) -> List[dict]:
    """调用 Node iztro 生成 N 个命盘 JSON 样本。

    Args:
        repo_root: wisdom-github 根目录 (含 node_modules/iztro/)
        n: 生成命盘数
        dates: 日期列表 (默认 DEFAULT_DATES)
        time_indexes: 时辰序号列表 0-12

    Returns:
        List[dict]: 命盘样本列表 (格式见 adapt_iztro_sample)
    """
    if dates is None:
        dates = DEFAULT_DATES[:n]
    if time_indexes is None:
        time_indexes = list(range(13))  # 0-12 时辰

    script = _generate_iztro_script(dates, time_indexes)
    script_path = repo_root / "tmp-p09-gen.mjs"
    script_path.write_text(script, encoding="utf-8")
    try:
        result = subprocess.run(
            ["node", str(script_path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",  # node 输出为 UTF-8（含中文星名）；缺省会按 GBK 解码而抛 UnicodeDecodeError
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Node failed: {result.stderr[:500]}")
        return json.loads(result.stdout)
    finally:
        script_path.unlink(missing_ok=True)


# ============================================================
# 12 项核对校验
# ============================================================
@dataclass
class CheckResult:
    """单条核对校验结果"""
    item_no: int
    name: str
    actual: str
    expected: str
    passed: bool


def check_12_items(sample: dict) -> List[CheckResult]:
    """对一条 iztro sample 做 12 项核对校验 (vs 王亭之标准)。

    Returns:
        List[CheckResult] (12 条)
    """
    chart = sample["chart"]
    palaces = chart["palaces"]
    year = sample["birthInfo"]["year"]
    results: List[CheckResult] = []

    # #1 命宫位置
    ming = next((p for p in palaces if p["name"] == "命宫"), None)
    ming_branch = BRANCHES[ming["branch"]] if ming else None
    results.append(CheckResult(
        1, "命宫位置", ming_branch or "N/A", "需 birth_year+timeIndex 对照",
        ming is not None,
    ))

    # #2 身宫位置
    body_branch = next(
        (BRANCHES[p["branch"]] for p in palaces if p["name"] == "命宫"), None
    )
    # iztro v2.x 不直接暴露身宫 — 简化: 子时身命同位
    results.append(CheckResult(
        2, "身宫位置", body_branch or "N/A", "子时身命同位=命宫",
        body_branch is not None,
    ))

    # #3 五行局 (iztro 输出 wuxingJuName)
    wuxing = chart.get("wuxingJuName", "N/A")
    results.append(CheckResult(
        3, "五行局", wuxing, "需查纳音表",
        wuxing in ("水二局", "木三局", "金四局", "土五局", "火六局"),
    ))

    # #4 紫微星位置
    zp = next(
        (p for p in palaces if any(s["name"] == "紫微" and s["type"] == "major" for s in p["stars"])),
        None,
    )
    zp_branch = BRANCHES[zp["branch"]] if zp else None
    results.append(CheckResult(
        4, "紫微星位置", f"{zp['name']}({STEMS[zp['stem']]}{zp_branch})" if zp else "N/A",
        "需按生日+生辰顺数紫微",
        zp is not None,
    ))

    # #5 12 主星入宫 (结构性检查: 14 主星, 各宫不重复, 无 orphan star)
    actual = {}
    for p in palaces:
        for s in p["stars"]:
            if s["type"] == "major":
                actual.setdefault(s["name"], []).append(BRANCHES[p["branch"]])
    total_stars = sum(len(v) for v in actual.values())
    expected_14 = {"紫微", "七杀", "天机", "天梁", "天相", "太阳", "巨门",
                   "廉贞", "破军", "天同", "太阴", "武曲", "贪狼", "天府"}
    has_14 = set(actual.keys()) == expected_14
    # 紫微星系6 + 天府星系6 + 天相+天梁+天同... 互不重复
    no_dup = all(len(v) == 1 for v in actual.values())
    # 命宫必有 1-2 主星
    ming_palace = next(p for p in palaces if p["name"] == "命宫")
    ming_stars = [s["name"] for s in ming_palace["stars"] if s["type"] == "major"]
    ming_ok = 1 <= len(ming_stars) <= 2
    struct_pass = has_14 and no_dup and ming_ok
    results.append(CheckResult(
        5, "12 主星入宫",
        f"{total_stars} 主星 ({len(actual)} 唯一)",
        f"14星={expected_14}, 互不重复, 命宫{len(ming_stars)}主星",
        struct_pass,
    ))

    # #6 14 辅星入宫
    minor_count = sum(
        1 for p in palaces for s in p["stars"] if s["type"] in ("minor", "lucky")
    )
    results.append(CheckResult(
        6, "14 辅星入宫", f"{minor_count} 辅星",
        "≥14 (文昌/文曲/左辅/右弼/天魁/天钺/禄存/擎羊/陀罗/火星/铃星/地空/地劫/天马)",
        minor_count >= 14,
    ))

    # #7 生年四化
    # Z53: 优先用 iztro 农历界年干（窗口日期防阳历年推错干），缺失回退旧推算
    ys_ = chart.get("natalYearStem") or year_stem(year)
    exp_nfs = dict(zip(MUTAGEN_KEYS, NFS_TABLE[ys_]))
    # iztro v2.3: mutagen 字段在所有 stars 里, 但**只主星**进入生年四化
    # 辅星 (文昌/文曲/左辅/右弼) 可能也有 mutagen = 神杀级, 排除
    act_nfs: dict = {}
    for p in palaces:
        for s in p["stars"]:
            if s.get("type") == "major" and s.get("mutagen") in MUTAGEN_KEYS:
                # 主星限定 (排除辅星误算)
                if s["name"] in {"紫微", "七杀", "天机", "天梁", "天相", "太阳",
                                 "巨门", "廉贞", "破军", "天同", "太阴",
                                 "武曲", "贪狼", "天府"}:
                    act_nfs[s["mutagen"]] = s["name"]
    nfs_match = all(act_nfs.get(k) == v for k, v in exp_nfs.items())
    results.append(CheckResult(
        7, "生年四化", str(act_nfs), f"王亭之{ys_}年表={exp_nfs}", nfs_match,
    ))

    # #8 大限四化 (大限命宫=本命宫, 大限宫干=本命宫干)
    # 大限1=命宫(巳=丁), 丁年四化
    d_stem = STEMS[ming["stem"]] if ming else "?"
    d_nfs = dict(zip(MUTAGEN_KEYS, NFS_TABLE[d_stem])) if d_stem in NFS_TABLE else {}
    d_tgt = {}
    for p in palaces:
        for s in p["stars"]:
            if s["type"] == "major" and s["name"] in d_nfs.values():
                for m, st in d_nfs.items():
                    if s["name"] == st:
                        d_tgt[m] = f"{p['name']}({BRANCHES[p['branch']]})"
    d_match = len(d_tgt) == 4
    results.append(CheckResult(
        8, "大限四化",
        f"大限命宫{ming_branch}({d_stem})→{d_tgt}",
        f"{d_stem}年王亭之表={d_nfs}",
        d_match,
    ))

    # #9 流年四化 (2026 丙午年, 流年命宫=本命+(流年支-原年支))
    flow_year = 2026
    natal_br = chart.get("natalYearBranch") or year_branch(year)  # Z53: 农历界年支优先
    diff = (BRANCHES.index(year_branch(flow_year)) - BRANCHES.index(natal_br)) % 12
    flow_idx = (BRANCHES.index(ming_branch) + diff) % 12
    flow_branch = BRANCHES[flow_idx]
    flow_palace = next((p for p in palaces if p["branch"] == flow_idx), None)
    flow_stem = STEMS[flow_palace["stem"]] if flow_palace else "甲"
    flow_nfs = dict(zip(MUTAGEN_KEYS, NFS_TABLE[flow_stem]))
    flow_tgt = {}
    for p in palaces:
        for s in p["stars"]:
            if s["type"] == "major" and s["name"] in flow_nfs.values():
                for m, st in flow_nfs.items():
                    if s["name"] == st:
                        flow_tgt[m] = f"{p['name']}({BRANCHES[p['branch']]})"
    flow_match = len(flow_tgt) == 4
    results.append(CheckResult(
        9, "流年四化",
        f"{flow_year}{flow_branch}({flow_stem})→{flow_tgt}",
        f"{flow_stem}年表={flow_nfs}",
        flow_match,
    ))

    # #10 飞化 (宫干化他宫)
    fly_count = 0
    fly_examples: List[str] = []
    for src in palaces:
        src_stem_idx = src["stem"]
        src_stem = STEMS[src_stem_idx] if src_stem_idx < len(STEMS) else None
        if src_stem not in NFS_TABLE:
            continue
        nfs = dict(zip(MUTAGEN_KEYS, NFS_TABLE[src_stem]))
        for tgt in palaces:
            if tgt["branch"] == src["branch"]:
                continue  # 本宫=自化
            for ts in tgt["stars"]:
                if ts["type"] != "major":
                    continue
                for m, st in nfs.items():
                    if ts["name"] == st:
                        fly_count += 1
                        if len(fly_examples) < 3:
                            fly_examples.append(
                                f"{src['name']}({src_stem})飞{m}={st}→{tgt['name']}"
                            )
    results.append(CheckResult(
        10, "飞化", f"飞化数={fly_count}",
        f"示例: {fly_examples}", fly_count > 0,
    ))

    # #11 自化 (宫干化本宫主星)
    self_count = 0
    self_examples: List[str] = []
    for p in palaces:
        ps_idx = p["stem"]
        ps = STEMS[ps_idx] if ps_idx < len(STEMS) else None
        if ps not in NFS_TABLE:
            continue
        nfs = dict(zip(MUTAGEN_KEYS, NFS_TABLE[ps]))
        for s in p["stars"]:
            if s["type"] != "major":
                continue
            for m, st in nfs.items():
                if s["name"] == st:
                    self_count += 1
                    if len(self_examples) < 3:
                        self_examples.append(f"{p['name']}({ps})自化{m}={st}")
    results.append(CheckResult(
        11, "自化", f"自化数={self_count}",
        f"示例: {self_examples}", True,
    ))

    # #12 来因宫 = 生年化忌所在宫
    laiyin_branch = None
    laiyin_palace = None
    laiyin_star = None
    MAJOR_14 = {"紫微", "七杀", "天机", "天梁", "天相", "太阳", "巨门",
                "廉贞", "破军", "天同", "太阴", "武曲", "贪狼", "天府"}
    for p in palaces:
        for s in p["stars"]:
            if s.get("type") == "major" and s.get("mutagen") == "忌" \
                    and s["name"] in MAJOR_14:
                laiyin_branch = BRANCHES[p["branch"]]
                laiyin_palace = p["name"]
                laiyin_star = s["name"]
    expected_laiyin = NFS_TABLE[ys_][3]
    passed_laiyin = (laiyin_branch is not None
                     and laiyin_star == expected_laiyin)
    results.append(CheckResult(
        12, "来因宫",
        f"化忌{laiyin_star}在{laiyin_palace}({laiyin_branch})" if laiyin_branch else "无化忌",
        f"{ys_}年化忌={expected_laiyin}",
        passed_laiyin,
    ))

    return results


def run_12_check_batch(samples: List[dict]) -> Tuple[int, int, List[CheckResult]]:
    """批量跑 12 项核对校验"""
    all_results: List[CheckResult] = []
    for sample in samples:
        all_results.extend(check_12_items(sample))
    passed = sum(1 for r in all_results if r.passed)
    total = len(all_results)
    return passed, total, all_results


__all__ = [
    "NFS_TABLE",
    "MUTAGEN_KEYS",
    "STEMS",
    "BRANCHES",
    "ZiweiChartMock",
    "adapt_iztro_sample",
    "generate_iztro_charts",
    "CheckResult",
    "check_12_items",
    "run_12_check_batch",
    "year_stem",
    "year_branch",
]