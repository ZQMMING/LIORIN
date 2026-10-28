"""河洛 × 黄历桥接（H9b: heluo_lunar_bridge）

职责：河洛流日应期段挂载黄历标注（农历/日柱/纳音/节气/宜忌）。
数据源：
  1. 注入优先（huangli_day）：主工作区黄历引擎（HuangliEngine.get_day）产物 dict，
     字段对齐 HuangliDay 子集（day_ganzhi/lunar_month/lunar_day/jie_qi/yi/ji…）；
  2. 兜底 lunar_python（独立包已声明依赖）：自产农历/日柱/纳音/节气，
     保证河洛引擎独立可跑（GitHub 分支最终可用）。
标注字段（宁漏勿错，来源可溯）：
  - solar_date / lunar / day_ganzhi / day_nayin / jie_qi / yi / ji / source
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HeluoLunarAnno:
    """流日段黄历标注。"""
    solar_date: str                 # 公历 YYYY-MM-DD（段首日）
    lunar: str = ""                 # 农历（如 十一月 初十）
    day_ganzhi: str = ""            # 日柱干支（如 甲子）
    day_nayin: str = ""             # 日纳音（如 海中金）
    jie_qi: str = ""                # 当日交节名（非交节日为空）
    yi: list = field(default_factory=list)      # 宜（仅注入黄历有）
    ji: list = field(default_factory=list)      # 忌（仅注入黄历有）
    source: str = "lunar_python"    # lunar_python | huangli_engine

    def to_dict(self) -> dict:
        return {
            "solar_date": self.solar_date,
            "lunar": self.lunar,
            "day_ganzhi": self.day_ganzhi,
            "day_nayin": self.day_nayin,
            "jie_qi": self.jie_qi,
            "yi": list(self.yi),
            "ji": list(self.ji),
            "source": self.source,
        }


def _lunar_python_anno(solar_date: str) -> HeluoLunarAnno:
    """lunar_python 兜底产黄历标注。"""
    try:
        from lunar_python import Solar
        y, m, d = map(int, solar_date.split("-")[:3])
        s = Solar.fromYmdHms(y, m, d, 12, 0, 0)
        l = s.getLunar()
        jq = l.getJieQi()
        return HeluoLunarAnno(
            solar_date=solar_date,
            lunar=f"{l.getMonthInChinese()}月 {l.getDayInChinese()}",
            day_ganzhi=l.getDayInGanZhi(),
            day_nayin=l.getDayNaYin(),
            jie_qi=jq or "",
            source="lunar_python",
        )
    except Exception:
        return HeluoLunarAnno(solar_date=solar_date, source="lunar_python")


def _huangli_day_anno(solar_date: str, hd: dict) -> HeluoLunarAnno:
    """主工作区黄历引擎产物（HuangliDay dict）映射为标注。"""
    lunar_month = hd.get("lunar_month", "")
    lunar_day = hd.get("lunar_day", "")
    lunar = f"{lunar_month}月 {lunar_day}" if lunar_month or lunar_day else ""
    return HeluoLunarAnno(
        solar_date=solar_date,
        lunar=lunar,
        day_ganzhi=hd.get("day_ganzhi", ""),
        day_nayin=hd.get("day_na_yin", ""),
        jie_qi=hd.get("jie_qi", ""),
        yi=list(hd.get("yi") or []),
        ji=list(hd.get("ji") or []),
        source="huangli_engine",
    )


def _as_huangli_dict(huangli_day: object) -> dict:
    """把黄历引擎产物统一成 dict。

    主仓 `HuangliEngine.get_day(date)` 返回的是 **dataclass `HuangliDay`**，
    而本桥接层要 dict；主仓侧**没有任何代码做这次转换**（河洛拆包后断链）。
    故此处**直接吃对象**：有 ``to_dict()`` 就调它，兼容 dict 与 dataclass 两种形态 ——
    平台侧接线因此只需一行 ``huangli_provider=lambda d: huangli_engine.get_day(d)``。
    """
    if huangli_day is None:
        return {}
    if isinstance(huangli_day, dict):
        return huangli_day
    to_dict = getattr(huangli_day, "to_dict", None)
    if callable(to_dict):
        try:
            out = to_dict()
            return out if isinstance(out, dict) else {}
        except Exception:
            return {}
    return {}


def annotate_day(solar_date: str, huangli_day: object = None) -> dict:
    """对流日段首日做黄历标注。

    Args:
        solar_date: 公历日期 YYYY-MM-DD
        huangli_day: 黄历引擎产物 —— **dict 或 dataclass 均可**
            （主仓 `HuangliEngine.get_day(date)` 返回 `HuangliDay` dataclass）；
            缺省则 lunar_python 兜底。
    """
    hd = _as_huangli_dict(huangli_day)
    if hd.get("day_ganzhi"):
        return _huangli_day_anno(solar_date, hd).to_dict()
    return _lunar_python_anno(solar_date).to_dict()


def annotate_liuri_yao(liuri_yao: dict | None, solar_date: str,
                       huangli_day: dict | None = None) -> dict | None:
    """流日判词挂黄历标注（原位挂载，不覆盖判词）。"""
    if liuri_yao is None:
        return None
    out = dict(liuri_yao)
    out["lunar"] = annotate_day(solar_date, huangli_day)
    return out
