# -*- coding: utf-8 -*-
"""L4 格局高低（B 块）—— 两层字段（裁143丙 + 裁144丙 + 边界）

层1  gaodi_qingli（判据层，PZZQ 十二章）
    值域二维: qing ∈ {ZHI, FEI_ZHI, WU}
            li   ∈ {QUAN, FEI_QUAN, WU}
    依据: PZZQ L1474/L1496/L1526/L1534/L1535/L1543（沈孝瞻原文，非徐注）
    分级: BOOK_CITED（定性判据）+ ENGINE_DEFINED_PENDING（量化阈值）

层2  gaodi_label（结果层，DTS §五 何知章）
    值域: FU / GUI / PIN / JIAN
    依据: DTS L347/L351/L355/L359（§五 何知章）
    分级: DTS_CITED
    ★ 切片 GAO_DI.001-.005 标「§二十五」有误，实际在 §五 L346-L375

映射  判据层 → 结果层（ENGINE_DEFINED，PZZQ 未给显式映射）
    qing=ZHI + li=QUAN   → FU / GUI
    qing=FEI_ZHI 或 li=FEI_QUAN → ZHONG（次高）
    qing=WU 或 li=WU     → PIN / JIAN

cheng_bai 参考（裁144丙 + 边界）:
    NO_GE  → gaodi_qingli = NOT_APPLICABLE
    其他三态 → gaodi 独立判，cheng_bai 只作 note 附注

★ 初版说明:
  定性判据有 PZZQ 原文（BOOK_CITED）。
  量化阈值（什么算"根深"/"通根"/"旺"）PZZQ 无阈值，标 ENGINE_DEFINED_PENDING。
  本模块初版只落结构 + 二维值域声明，不含量化判定逻辑。
  量化判定待案例反标定后补。
"""
from typing import Any, Dict, Optional, Tuple

# ------------------------------------------------------------------
# 二维值域枚举
# ------------------------------------------------------------------
QING_VALUES = ("ZHI", "FEI_ZHI", "WU")
LI_VALUES   = ("QUAN", "FEI_QUAN", "WU")

# 组合 → 结果标签映射（ENGINE_DEFINED）
# 依据: PZZQ L1526「有情而兼有力…格之最高」/ L1534「非情之至」/ L1535「非力之全」
#       DTS L347/L351 富贵 / L355/L359 贫贱
QING_LI_TO_LABEL = {
    ("ZHI", "QUAN"):     "FU_GUI",       # 最高: 有情而兼有力
    ("FEI_ZHI", "QUAN"): "ZHONG",        # 次高: 情不至
    ("ZHI", "FEI_QUAN"): "ZHONG",        # 次高: 力不全
    ("FEI_ZHI", "FEI_QUAN"): "ZHONG",    # 双不全
    ("WU", "QUAN"):      "PIN_JIAN",     # 无情有力
    ("QUAN", "WU"):      "PIN_JIAN",     # 有力无情
    ("WU", "WU"):        "BUDING",       # 双无
    ("ZHI", "WU"):       "PIN_JIAN",     # 有情无力
    ("FEI_ZHI", "WU"):   "PIN_JIAN",
}


def compute_gaodi_qingli(
    qing: str,
    li: str,
    cheng_bai: Optional[str] = None,
) -> Dict[str, Any]:
    """层1: 判据层（PZZQ 十二章 有情/有力 二维）

    Args:
        qing: ZHI / FEI_ZHI / WU
        li:   QUAN / FEI_QUAN / WU
        cheng_bai: 可选，cheng_bai.value（CHENG/CHENG_ZHONG_YOU_PO/PO/None）

    Returns:
        {
            "qingli": {"qing": str, "li": str},
            "label": str,          # 层2 结果标签
            "cheng_bai_note": str|None,
            "evidence": {
                "pzzq_lines": [1474, 1526, 1534, 1535, 1543],
                "dts_lines": [347, 351, 355, 359],
                "slice_ids": "STRUCTURE.GE_JU.GAO_DI.001..008",
            },
            "evidence_grade": "BOOK_CITED + ENGINE_DEFINED_PENDING(量化阈值)",
        }
    """
    if cheng_bai is None or cheng_bai == "NO_GE":
        return {
            "qingli": None,
            "label": "NOT_APPLICABLE",
            "cheng_bai_note": "无格，不判高低",
            "evidence": {"slice_ids": "STRUCTURE.GE_JU.GAO_DI.001..008"},
            "evidence_grade": "BOOK_CITED",
        }

    label = QING_LI_TO_LABEL.get((qing, li), "PIN_JIAN")
    note = None
    if cheng_bai == "CHENG_ZHONG_YOU_PO":
        note = "成中有败，层次受损"
    elif cheng_bai == "PO":
        note = "破格盘，破中之高/低"

    return {
        "qingli": {"qing": qing, "li": li},
        "label": label,
        "cheng_bai_note": note,
        "evidence": {
            "pzzq_lines": [1474, 1526, 1534, 1535, 1543],
            "dts_lines": [347, 351, 355, 359],
            "slice_ids": "STRUCTURE.GE_JU.GAO_DI.001..008",
        },
        "evidence_grade": "BOOK_CITED(定性) + ENGINE_DEFINED_PENDING(量化阈值)",
    }


def compute_gaodi_label(qingli: Optional[Dict[str, str]]) -> str:
    """层2: 结果层（DTS §五 何知章 富贵贫贱）

    从 qingli 二维值映射到标签。
    """
    if not qingli:
        return "NOT_APPLICABLE"
    qing = qingli.get("qing", "WU")
    li = qingli.get("li", "WU")
    return QING_LI_TO_LABEL.get((qing, li), "PIN_JIAN")


if __name__ == "__main__":
    # 探针（独立进程，不 import 引擎生产路径）
    print("=== gaodi 两层字段探针（独立进程）===")

    # P6 三维验证
    tests = [
        # (qing, li, cheng_bai, 预期 label)
        ("ZHI", "QUAN", "CHENG", "FU_GUI"),
        ("FEI_ZHI", "QUAN", "CHENG", "ZHONG"),
        ("ZHI", "FEI_QUAN", "CHENG", "ZHONG"),
        ("WU", "WU", "CHENG", "BUDING"),
        ("ZHI", "QUAN", "CHENG_ZHONG_YOU_PO", "FU_GUI"),  # note 附注
        ("ZHI", "QUAN", "PO", "FU_GUI"),                   # note 附注
        ("ZHI", "QUAN", None, "NOT_APPLICABLE"),           # NO_GE 边界
    ]
    all_pass = True
    for qing, li, cb, expect in tests:
        r = compute_gaodi_qingli(qing, li, cb)
        ok = r["label"] == expect
        all_pass &= ok
        print("  qing=%-8s li=%-10s cb=%-22s 预期=%-16s 实测=%-16s %s note=%s"
              % (qing, li, str(cb), expect, r["label"],
                 "PASS" if ok else "FAIL", r.get("cheng_bai_note")))

    print("★ 探针:", "PASS" if all_pass else "FAIL")
    print("★ 量化阈值: ENGINE_DEFINED_PENDING（PZZQ 无阈值，待案例反标定）")
