# -*- coding: utf-8 -*-
"""双轨对照 · 藏干表（裁一百零七丙 收窄版 + 一百一十四乙）

★ 两轨【独立生成】, 不共享任何中间步骤:
  轨A  从六本原文【逐字抄】—— 不 import 引擎, 不读 zhi_hidden_stems_v1.json
       来源1  SFTK L4057  「十二支中所藏法」= 藏干清单
       来源2  PZZQ L2917/L2918 = 次序定义（本气/方生/寄生）
       对照  DTS L225/L230（用事格式）并列记录
  轨B  引擎实测 ten_god(日主, 藏干) + HIDDEN 表

判据（裁一百一十二/一百一十三共用）:
  集合相同 → 不冲突（排序维度不同无所谓）
  集合不同 → 真冲突

★ 预期表已废除（裁一百一十一甲）—— 原表由我手填, 本轮已在它上面错两处。
"""
import sys
import os
import io
import re

ROOT = r"D:/shuntian-ziping-p0"
RAW = os.path.join(ROOT, "registries", "source", "raw")
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
# ★ 轨B 才准 import 引擎; 轨A 全程不碰
from engines.common.l0_fact_builder import ten_god, HIDDEN

Z = list("子丑寅卯辰巳午未申酉戌亥")

# ── 轨A: 从 SFTK L4057 逐字抄（不改一字, 只解析次序）──
# 原文: 「子藏癸水是祿位。丑己三分辛及癸。寅藏甲丙戊木火。辰有戊兮乙與癸。
#        巳藏丙戊及庚金。午宮卻有丁火。己未宮丁乙己同臨。申宮庚金壬水戊。
#        酉宮辛金一位美。戌有丁辛戊土至亥藏壬甲二天干。十二宮中須記取。」
SFTK_L4057 = ("子藏癸水是祿位。丑己三分辛及癸。寅藏甲丙戊木火。辰有戊兮乙與癸。"
              "巳藏丙戊及庚金。午宮卻有丁火。己未宮丁乙己同臨。申宮庚金壬水戊。"
              "酉宮辛金一位美。戌有丁辛戊土至亥藏壬甲二天干。十二宮中須記取。")

# 解析: 按支名切段, 段内抽干（保留原文出现次序）
SEG_SPLIT = re.compile(r"[子丑寅卯辰巳午未申酉戌亥]")


def parse_track_a():
    """从 SFTK 原句解析「支 → 有序藏干列表」。★ 不查任何引擎数据。"""
    out = {}
    marks = [(m.start(), m.group(0)) for m in SEG_SPLIT.finditer(SFTK_L4057)]
    for i, (pos, z) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(SFTK_L4057)
        seg = SFTK_L4057[pos + 1:end]
        gans = re.findall(r"[甲乙丙丁戊己庚辛壬癸]", seg)
        # 去重但保序
        seen = set()
        ordered = []
        for g in gans:
            if g not in seen:
                seen.add(g)
                ordered.append(g)
        out[z] = ordered
    return out


# ── DTS 对照行（逐字抄, 不解释）──
DTS_TRACKS = {
    "寅": {"set": ["戊", "丙", "甲"], "order": ["戊", "丙", "甲"],
           "src": "DTS L225「寅月生人，立春后七日前，皆值戊土用事；"
                  "八日后十四日前者，丙火用事；十五日后，甲木用事」"},
    "子": {"set": ["壬", "癸"], "order": ["壬", "癸"],
           "src": "DTS L230「子时生人，前三刻，三分壬水用事；"
                  "后四刻，七分癸水用事」"},
}


def main():
    print("=" * 100)
    print("双轨对照 · 藏干表（轨A = 六本原文逐字抄 / 轨B = 引擎实测）")
    print("=" * 100)
    print("★ 脚本: D:/shuntian-ziping-p0/scripts/probe_l2_canggan_dual.py")
    print("★ 轨A 不 import 引擎、不读 zhi_hidden_stems_v1.json —— 与轨B 无共享")

    A = parse_track_a()
    B = {z: list(HIDDEN.get(z) or []) for z in Z}

    print("\n" + "=" * 100)
    print("轨A（SFTK L4057「十二支中所藏法」逐字解析）")
    print("-" * 100)
    for z in Z:
        print("   %s  轨A=%-12s 轨B=%-12s" % (z, " ".join(A.get(z, [])) or "(无)",
                                          " ".join(B[z]) or "(无)"))

    # ── 集合对照判据 ──
    print("\n" + "=" * 100)
    print("判据一：集合对照（集合相同=不冲突 / 集合不同=真冲突）")
    print("-" * 100)
    set_eq, set_ne, set_miss = [], [], []
    for z in Z:
        sa, sb = set(A.get(z, [])), set(B[z])
        if not sa:
            set_miss.append(z)
            print("   %s  ★ 轨A 未解析出（待人工核原句）" % z)
            continue
        if sa == sb:
            set_eq.append(z)
            print("   %s  集合相同 %s   → 不冲突" % (z, sorted(sa)))
        else:
            only_a = sorted(sa - sb)
            only_b = sorted(sb - sa)
            set_ne.append((z, only_a, only_b))
            print("   %s  ★集合不同: 轨A独有 %s / 轨B独有 %s  → 真冲突"
                  % (z, only_a, only_b))

    # ── 次序对照（集合相同时才看次序）──
    print("\n" + "=" * 100)
    print("判据二：次序对照（仅对集合相同的支）")
    print("-" * 100)
    for z in set_eq:
        if A.get(z) != B[z]:
            print("   %s  集合同、顺序不同: 轨A %s / 轨B %s  → 排序维度差, 非冲突"
                  % (z, " ".join(A[z]), " ".join(B[z])))
        else:
            print("   %s  集合同、顺序同  → 完全一致" % z)

    # ── DTS 对照行 ──
    print("\n" + "=" * 100)
    print("判据三：DTS 用事格式 对照（裁一百一十四：轨A 并列记录）")
    print("-" * 100)
    for z, d in DTS_TRACKS.items():
        sa, sb = set(A.get(z, [])), set(B[z])
        sd = set(d["set"])
        v1 = "集合同" if sd == sb else "★集合不同"
        v2 = "集合同" if sd == sa else "★集合不同"
        print("\n   【%s】%s" % (z, d["src"][:70]))
        print("      DTS 用事集 = %s" % sorted(sd))
        print("      轨A 集     = %s   → 与 DTS %s" % (sorted(sa), v2))
        print("      轨B 集     = %s   → 与 DTS %s" % (sorted(sb), v1))
        if sd == sb and d["order"] != B[z]:
            print("      ★ 与轨B 集合同、顺序不同 → 排序维度差, 非冲突")

    # ── 汇总 ──
    print("\n" + "=" * 100)
    print("汇总（★ 脚本【不出】最终结论, 只出对照事实）")
    print("=" * 100)
    print("   轨A vs 轨B  集合相同 %d 支 / 集合不同 %d 支 / 轨A未解析 %d 支"
          % (len(set_eq), len(set_ne), len(set_miss)))
    print("   DTS 对照    寅: 集合同·顺序差   子: ★集合不同（已裁为真冲突）")
    print("\n   ★ 待人工裁定:")
    for z, oa, ob in set_ne:
        print("      %s 轨A独有 %s / 轨B独有 %s" % (z, oa, ob))
    for z in set_miss:
        print("      %s 轨A 未解析出 —— 需人工读 SFTK 原句" % z)


if __name__ == "__main__":
    main()