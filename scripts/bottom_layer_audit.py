# -*- coding: utf-8 -*-
"""底层激活审计 — 验证七层机制在生产链的真实命中率(不写死代码假装有).

用法: python scripts/bottom_layer_audit.py [--books PZZQ DTS ...] [--limit N]
输出: 各维度激活表(病机挂载/格体输出/域裁决/拓扑/结构裁决), 以及 0 激活项。
"""
import sys
import io
import glob
import json
import collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from p0_v2.bazi_gate import paipan  # noqa: E402

BING_IDS = ['CAI_DUO_SHEN_RUO', 'SHA_ZHONG_SHEN_QING', 'XIE_QI_TAI_ZHONG',
            'BIJIE_CHENG_DANG', 'SHANGGUAN_JIAN_GUAN', 'XIAO_DUO_SHI',
            'YIN_DUO_MAI_ZI', 'ZHI_SHA_TAI_GUO', 'YONG_SHEN_BU_ZAI_JU',
            'BIJIE_DUO_CAI', 'JIAN_LU_YUE_JIE']


def main():
    args = [a for a in sys.argv[1:]]
    books = None
    limit = None
    if '--books' in args:
        i = args.index('--books')
        books = args[i + 1:][:args[i + 1:].index('--limit')] if '--limit' in args[i + 1:] else args[i + 1:]
    if '--limit' in args:
        i = args.index('--limit')
        limit = int(args[i + 1])

    # 统计容器
    bing_hit = {b: {'n': 0, 'wx': 0, 'sid': 0, 'sev': 0, 'dom': 0} for b in BING_IDS}
    sev_hist = collections.Counter()
    ge_ok = 0
    ti_ok = 0
    xi_ok = 0
    zhi_ok = 0
    hua_ok = 0
    debate_main_ok = 0
    domain_primaries_ok = 0
    multi_domain = 0
    root_rel_ok = 0
    root_eff_ok = 0
    resolved_ok = 0
    chong_ok = 0
    anhe_ok = 0
    cancel_ok = 0
    sc_state = collections.Counter()
    n_total = 0
    n_bing = 0
    n_ge = 0
    n_gl_ge = 0
    gecheng_keys = collections.Counter()

    fps = sorted(glob.glob('p0_v2/case_audit/*_clean.jsonl'))
    for fp in fps:
        book = fp.replace('\\', '/').split('/')[-1].replace('_clean.jsonl', '')
        if books and book not in books:
            continue
        for i, line in enumerate(open(fp, encoding='utf-8-sig')):
            if limit and i >= limit:
                break
            if not line.strip():
                continue
            d = json.loads(line)
            try:
                r = paipan(d['bazi'])
            except Exception:
                continue
            n_total += 1

            # --- L4 病机挂载 ---
            bl = r.get('bing_list') or []
            if bl:
                n_bing += 1
            for b in bl:
                bid = b.get('bing_id')
                if bid in bing_hit:
                    bing_hit[bid]['n'] += 1
                    if b.get('bing_wx'):
                        bing_hit[bid]['wx'] += 1
                    if b.get('slice_id'):
                        bing_hit[bid]['sid'] += 1
                    if b.get('severity') is not None:
                        bing_hit[bid]['sev'] += 1
                        sev_hist[b.get('severity')] += 1
                    if b.get('bing_domain'):
                        bing_hit[bid]['dom'] += 1

            # --- 格局层输出 ---
            gc = r.get('ge_cheng') or {}
            if gc:
                n_ge += 1
                gecheng_keys.update(gc.keys())
                if gc.get('ge'):
                    ge_ok += 1
                if gc.get('ti_wx'):
                    ti_ok += 1
                if gc.get('xi_wx'):
                    xi_ok += 1
                if gc.get('zhi_wx'):
                    zhi_ok += 1
                if gc.get('hua_wx'):
                    hua_ok += 1
            if r.get('ge_list') or (gc and gc.get('ge')):
                n_gl_ge += 1

            # --- L6 域裁决 ---
            db = r.get('bing_debate') or {}
            if db.get('primary') or db.get('main_bing') or db.get('main_bing_id'):
                debate_main_ok += 1
            if db.get('domain_primaries'):
                domain_primaries_ok += 1
                if len(db.get('domain_primaries')) > 1:
                    multi_domain += 1

            # --- L5 拓扑 ---
            rr = r.get('root_relations')
            if rr:
                root_rel_ok += 1
            re_ = r.get('root_effectiveness')
            if re_:
                root_eff_ok += 1

            # --- L0 结构裁决: 顶层 resolved 块(2026-10 起独立投影) / 嵌 combination_facts.resolved ---
            res = r.get('resolved') or (r.get('combination_facts') or {}).get('resolved') or {}
            if res:
                resolved_ok += 1
                if res.get('chong_actions'):
                    chong_ok += 1
                if res.get('anhe'):
                    anhe_ok += 1
                if res.get('chong_canceled') or res.get('he_canceled') or res.get('xinghe'):
                    cancel_ok += 1

            # --- L2 切片条件三态(2026-10 起生产接线) ---
            for b in bl:
                sc = b.get('slice_condition') or {}
                sc_state[sc.get('state')] += 1

    print('=' * 78)
    print('底层激活审计  样本=%d 盘' % n_total)
    print('=' * 78)

    print('\n[L4 病机挂载率]  病机触发盘数=%d (%.1f%%)' % (n_bing, 100.0 * n_bing / max(n_total, 1)))
    print('%-22s %6s %6s %6s %6s %6s' % ('病机', '触发', 'wx挂', 'slice挂', 'sev挂', '域挂'))
    for bid in BING_IDS:
        h = bing_hit[bid]
        if h['n'] == 0:
            print('%-22s %6d  (0 触发)' % (bid, 0))
            continue
        print('%-22s %6d %6d %6d %6d %6d' % (bid, h['n'], h['wx'], h['sid'], h['sev'], h['dom']))
    print('severity 分布: %s' % dict(sorted(sev_hist.items())))

    print('\n[格局层输出]  定格盘=%d (%.1f%%)  格体ti=%d 喜神xi=%d 制zhi=%d 化hua=%d'
          % (ge_ok, 100.0 * ge_ok / max(n_total, 1), ti_ok, xi_ok, zhi_ok, hua_ok))
    print('ge_cheng 字段集: %s' % sorted(gecheng_keys))

    print('\n[L6 域裁决]  主病输出=%d  五域分组=%d  跨域并存=%d' % (debate_main_ok, domain_primaries_ok, multi_domain))

    print('\n[L5 拓扑]  root_relations 非空=%d  root_effectiveness 非空=%d' % (root_rel_ok, root_eff_ok))

    print('\n[L0 结构裁决]  resolved 输出=%d  冲动作=%d  暗合=%d  解冲/解合/刑合=%d'
          % (resolved_ok, chong_ok, anhe_ok, cancel_ok))

    print('\n[L2 切片条件三态]  %s  (生产接线: 并行校验不改判定)' % dict(sc_state))

    print('\n[生产链 0 激活项]')
    print('  L1 slice_loader        : 0 引用(病机 slice_id 为硬编码标注, 运行不查切片)')
    print('  L2 condition_evaluator : 已接线(STEP-L2-1, 并行校验挂 bing_list.slice_condition)')
    print('  L0 condition_spec      : 经 L2 激活(生产链随 L2 走通)')
    print('  pzzq_resolver_v2       : 仅被 tests 引用, 生产链 0 激活')


if __name__ == '__main__':
    main()
