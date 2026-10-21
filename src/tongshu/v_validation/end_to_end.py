"""端到端验证脚本：人生时间轴回测

对单个命例进行完整人生时间线回测，验证系统在不同年份的预测能力。

使用方式:
    cd ./backend
    PYTHONPATH=src python -m tongshu.v_validation.end_to_end
"""
from __future__ import annotations
import sys
import json
import logging
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path("./src")))

from tongshu.v_validation import (
    Case, Event, EvidenceGrade, EventSeverity, EventCategory,
    BacktestEngine, BlindProtocol, ScoringMatrix,
    AblationRunner, BaselineSystem, ValidationReport,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── 种子案例（纪晓岚） ───────────────────────────────────────────────
# 公历 1724-08-03 午时，已知历史事件
SEED_CASE = Case(
    case_id="GOLDEN-JIXIAOLAN",
    gender="male",
    birth_year=1724, birth_month=8, birth_day=3, birth_hour=12,
    birth_location="Xian County, Hebei",
    timezone="Asia/Shanghai",
    events=[
        Event(date=date(1749, 3, 15), category=EventCategory.JOB_CHANGE,
              severity=EventSeverity.MAJOR, description="中举",
              evidence_grade=EvidenceGrade.B),
        Event(date=date(1754, 6, 20), category=EventCategory.JOB_CHANGE,
              severity=EventSeverity.MAJOR, description="中进士",
              evidence_grade=EvidenceGrade.A),
        Event(date=date(1766, 1, 10), category=EventCategory.PROMOTION,
              severity=EventSeverity.MODERATE, description="任职翰林院",
              evidence_grade=EvidenceGrade.B),
        Event(date=date(1780, 9, 5), category=EventCategory.PROMOTION,
              severity=EventSeverity.MAJOR, description="官至体仁阁大学士",
              evidence_grade=EvidenceGrade.A),
    ],
    source_type="historical",
    source_url="https://en.wikipedia.org/wiki/Ji_Xiaolan",
)


def run_end_to_end():
    """运行端到端验证流程。"""
    logger.info("=" * 60)
    logger.info("SHUNTIAN V-Validation — End-to-End Verification")
    logger.info("=" * 60)

    # ── Phase 1: L0-L2 算法正确性 ──
    logger.info("[Phase 1] Algorithm Correctness (L0-L2)")
    from tongshu.engines.bazi_engine import BaziEngine, pillar_to_chinese
    from tongshu.engines.ziwei_engine import ZiweiEngine

    bazi = BaziEngine().compute(SEED_CASE.birth_date_tuple, gender=SEED_CASE.gender)
    logger.info(f"  Bazi: {bazi.year_pillar} {bazi.month_pillar} {bazi.day_pillar} {bazi.hour_pillar}")

    # V2.6 fix: 紫微用农历输入, 阳历->lunar_python转农历tuple(原传阳历字符串导致iztro报错)
    from lunar_python import Solar as _Solar
    _solar = _Solar.fromYmdHms(SEED_CASE.birth_year, SEED_CASE.birth_month, SEED_CASE.birth_day, SEED_CASE.birth_hour, 0, 0)
    _lunar = _solar.getLunar()
    _lunar_date = (_lunar.getYear(), _lunar.getMonth(), _lunar.getDay())
    ziwei = ZiweiEngine().compute(_lunar_date, SEED_CASE.birth_hour, gender=SEED_CASE.gender)
    stars = getattr(ziwei, 'stars', None) or getattr(ziwei, 'main_stars', None) or []
    logger.info(f"  Ziwei: main stars={stars[:3] if stars else 'N/A'}")

    # ── Phase 2: L3 历史回测 ──
    logger.info("[Phase 2] Historical Backtest (L3)")
    engine = BacktestEngine()
    results = engine.run(SEED_CASE, start_year=1740, end_year=1790)
    stats = engine.aggregate_stats()
    logger.info(f"  Years tested: {stats['total_years']}")
    logger.info(f"  Mean precision: {stats['mean_precision']:.2%}")
    logger.info(f"  Mean recall: {stats['mean_recall']:.2%}")
    logger.info(f"  Mean F1: {stats['mean_f1']:.2%}")

    # ── Phase 3: 盲测 ──
    logger.info("[Phase 3] Blind Test Protocol (L3)")
    blind = BlindProtocol([SEED_CASE])
    run = blind.run(SEED_CASE, start_year=1740, end_year=1790)
    logger.info(f"  Predictions made: {len(run.predictions)} years")
    logger.info(f"  Results revealed: {run.revealed_results is not None}")

    # ── Phase 4: 消融实验 ──
    logger.info("[Phase 4] Ablation Experiment (L4)")
    ablation = AblationRunner(SEED_CASE)
    ablation_results = ablation.run()
    report_data = ablation.generate_report()
    logger.info(f"  Full model score: {report_data['full_score']:.1f}")
    for var, info in report_data['variants'].items():
        if var != "full":
            logger.info(f"  {var}: score={info['score']:.1f} delta={info['delta']:+.1f}")

    # ── Phase 5: 基线对比 ──
    logger.info("[Phase 5] Baseline Comparison (L4)")
    baseline = BaselineSystem()
    baseline.run_all([SEED_CASE])
    comparison = baseline.get_comparison()
    for name, metrics in comparison.items():
        logger.info(f"  {name:15s} F1={metrics['f1']:.2%} Major Recall={metrics['major_event_recall']:.2%}")

    # ── Phase 6: 生成报告 ──
    logger.info("[Phase 6] Generating Validation Report")
    report = ValidationReport()
    report.add_section("summary", {
        "total_cases": 1,
        "total_events": len(SEED_CASE.events),
        "golden_events": len(SEED_CASE.golden_events),
        "major_events": len(SEED_CASE.major_events),
    })
    report.add_section("backtest_results", stats)
    report.add_section("ablation_results", report_data)
    report.add_section("baseline_comparison", comparison)
    report.add_section("recommendations", [
        "增加更多历史案例（目标: 50+ cases）",
        "建立Golden Dataset（只允许A/B级证据）",
        "实现真正的pipeline集成（当前使用模拟数据）",
        "制定前瞻冻结协议（V-FROZEN-2026-09-01）",
    ])

    output_path = Path("./backend/docs/validation_report.json")
    report.save(str(output_path))
    logger.info(f"  Report saved: {output_path}")

    logger.info("=" * 60)
    logger.info("V-VALIDATION COMPLETE")
    logger.info("=" * 60)
    return report.generate()


if __name__ == "__main__":
    result = run_end_to_end()
    print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
