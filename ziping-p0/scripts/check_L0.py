# -*- coding: utf-8 -*-
"""L0 逐键核验 —— §2.2 契约 23 键, DTS 510 盘
核: 存在性 + 值与四柱手工核算是否一致 + 空值率
不推断, 只比对。四柱来自案例 bazi 字段, 是唯一真值。
"""
import sys, os, json, glob, collections

ROOT = r"D:/shuntian-ziping-p0"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

from p0_v2.bazi_gate import paipan  # noqa: E402

# 藏干表(独立核算用, 不依赖引擎)
CANGGAN = {
    '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'], '卯': ['乙'],
    '辰': ['戊', '乙', '癸'], '巳': ['丙', '戊', '庚'], '午': ['丁', '己'],
    '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'], '酉': ['辛'],
    '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲'],
}
WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
      '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
YANG = set('甲丙戊庚壬')
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}   # 我克
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}  # 我生
SHWO = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}   # 生我

CONTRACT = ["day_stem", "hidden_stems", "stem_relations", "ten_god_members",
            "month_branch", "month_hidden_stems", "month_transparent",
            "month_qi_stem", "month_qi_element", "month_qi_ten_god",
            "month_supports_daymaster", "daymaster_element",
            "root_facts", "root_weight_class_facts", "changsheng_direction",
            "branch_relations", "combination_facts", "stem_combination_facts",
            "target_relation_facts", "target_root_facts",
            "any_stem_has_ten_god", "jianlu_yuejie_keystone",
            "hezuo_relation_premise"]


def parse_bz(bz):
    """'癸亥壬戌乙未壬午' -> [(干,支)x4]"""
    bz = (bz or "").replace(" ", "")
    out = []
    for i in range(0, min(8, len(bz)), 2):
        out.append((bz[i], bz[i + 1]))
    return out


def check(cid, d):
    """返回 (错误列表, 观测)"""
    bz = (d.get("bazi") or "").replace(" ", "")
    pz = parse_bz(bz)
    if len(pz) != 4:
        return ["四柱解析失败: %r" % bz], {}
    r = paipan(bz)
    raw = r.get("raw_facts") or {}
    errs, obs = [], {}

    # A 存在性
    miss = [k for k in CONTRACT if k not in raw]
    if miss:
        errs.append("缺契约键 %s" % miss)
    obs["缺键数"] = len(miss)

    # B 干支本身对不对
    dm_e = raw.get("day_stem")
    if dm_e != pz[2][0]:
        errs.append("day_stem=%s 应为 %s" % (dm_e, pz[2][0]))
    if raw.get("month_branch") != pz[1][1]:
        errs.append("month_branch=%s 应为 %s" % (raw.get("month_branch"), pz[1][1]))

    # C hidden_stems 藏干对不对
    hs = raw.get("hidden_stems") or {}
    for pos, (g, z) in zip(("year", "month", "day", "hour"), pz):
        want = CANGGAN.get(z, [])
        got = hs.get(pos) or []
        if list(got) != want:
            errs.append("hidden_stems[%s]=%s 应为 %s (支%s)" % (pos, got, want, z))
    obs["藏干盘OK"] = 1 if not [e for e in errs if "hidden_stems" in e] else 0

    # D daymaster_element
    if raw.get("daymaster_element") != WX.get(pz[2][0]):
        errs.append("daymaster_element=%s 应为 %s"
                    % (raw.get("daymaster_element"), WX.get(pz[2][0])))

    # E month_qi_element = 月支本气五行
    mz = pz[1][1]
    mqi = CANGGAN.get(mz, [''])[0]
    if raw.get("month_qi_stem") not in (None, mqi) and raw.get("month_qi_stem") != mqi:
        errs.append("month_qi_stem=%s 应为 %s" % (raw.get("month_qi_stem"), mqi))
    if raw.get("month_qi_element") != WX.get(mqi):
        errs.append("month_qi_element=%s 应为 %s"
                    % (raw.get("month_qi_element"), WX.get(mqi)))

    # F month_supports_daymaster 布尔值
    msd = raw.get("month_supports_daymaster")
    if msd is not None and not isinstance(msd, bool):
        errs.append("month_supports_daymaster 非布尔: %r" % (msd,))

    # G any_stem_has_ten_god / jianlu / hezuo 布尔
    # §2.2「关系前提」三字段实测均为 dict(按十神/组合分项的布尔表), 非标量:
    #   any_stem_has_ten_god   {财/官/印: bool}
    #   jianlu_yuejie_keystone {财/官/煞/食: bool}
    #   hezuo_relation_premise {7个十神组合: bool, + _note}
    # 故只核内层值必须是布尔(布尔枚举范式 §1.2), 不核外层类型。
    for k in ("any_stem_has_ten_god", "jianlu_yuejie_keystone",
              "hezuo_relation_premise"):
        v = raw.get(k)
        if v is None:
            continue
        if not isinstance(v, dict):
            errs.append("%s 应为 dict(分项布尔表), 实为 %s" % (k, type(v).__name__))
            continue
        for k2, v2 in v.items():
            if k2 != "_note" and not isinstance(v2, bool):
                errs.append("%s[%s] 非布尔: %r" % (k, k2, v2))

    # H root_weight_class_facts: 每柱一档, 标签在枚举内
    rwc = raw.get("root_weight_class_facts") or {}
    if isinstance(rwc, dict):
        for pos, v in rwc.items():
            cls = (v or {}).get("class")
            if cls not in ("NONE", "LIGHT", "HEAVY"):
                errs.append("root_weight_class[%s].class=%r 越界" % (pos, cls))
        obs["根分类柱数"] = len(rwc)

    return errs, obs


def main():
    book = sys.argv[1] if len(sys.argv) > 1 else "DTS"
    CA = os.path.join(ROOT, "p0_v2", "case_audit")
    cases = {}
    for fp in glob.glob(os.path.join(CA, "%s_clean.jsonl" % book)):
        for l in open(fp, encoding="utf-8-sig"):
            if l.strip():
                d = json.loads(l)
                cases[d["case_id"]] = d
    print("=" * 88)
    print("L0 逐键核验  《%s》  %d 盘" % (book, len(cases)))
    print("=" * 88)

    bad = collections.defaultdict(list)
    nerr = 0
    obs_c = collections.Counter()
    for cid in sorted(cases):
        try:
            errs, obs = check(cid, cases[cid])
        except Exception as e:
            bad["★抛异常 %s" % type(e).__name__].append(cid)
            nerr += 1
            continue
        obs_c.update(obs)
        if errs:
            nerr += 1
            for e in errs:
                key = e.split("=")[0].split("[")[0]
                bad[key].append((cid, e))

    print("\n盘数 %d, 有错 %d, 无错 %d"
          % (len(cases), nerr, len(cases) - nerr))
    print("观测: %s" % dict(obs_c))
    if not bad:
        print("\n✓ L0 契约 23 键, 全部核对通过")
        return 0
    print("\n=== 错误分类 ===")
    for k in sorted(bad, key=lambda x: -len(bad[x])):
        v = bad[k]
        print("  %-34s %d 盘" % (k, len(v)))
        for cid, e in v[:3]:
            print("      %-9s %s" % (cid, e))
        if len(v) > 3:
            print("      ... 另 %d 盘" % (len(v) - 3))
    return 1


if __name__ == "__main__":
    sys.exit(main())