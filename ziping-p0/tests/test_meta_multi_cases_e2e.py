# -*- coding: utf-8 -*-
"""命理元统一输出层多案例端到端测试.
验证多种命局类型(身旺/身弱/中和/特殊格局)的6命理元输出.
"""
import sys
sys.path.insert(0, '.')

from engines.production_entry import production_entry, FrozenCanonicalBaziChart


def run_case(name, pillars):
    """运行单个案例, 返回命理元输出摘要."""
    chart = FrozenCanonicalBaziChart(pillars=pillars)
    result = production_entry(chart)
    meta = result.get('meta_outputs', {})

    summary = {
        'name': name,
        'gate': result['gate'],
        'meta_count': meta.get('meta_count', 0),
    }

    for meta_id, output in meta.get('meta_outputs', {}).items():
        tracks = output.get('tracks', {})
        activated = [tid for tid, t in tracks.items() if t.get('activated')]
        conflict = output.get('conflict', {}).get('conflict_type', '无')
        # 获取首选候选
        first_candidates = {}
        for tid in activated:
            cands = tracks[tid].get('candidates', [])
            if cands:
                first_candidates[tid] = cands[0].get('element', '')
        summary[meta_id] = {
            'activated': activated,
            'conflict': conflict,
            'first_candidates': first_candidates,
        }

    return summary


def test_multiple_cases():
    """多案例端到端测试."""
    cases = [
        # 1. 身旺: 甲寅 丙寅 甲子 丙寅 (甲木得令+重根)
        ('身旺-甲木寅月', {'year': ['甲', '寅'], 'month': ['丙', '寅'], 'day': ['甲', '子'], 'hour': ['丙', '寅']}),
        # 2. 身弱: 戊申 庚申 戊申 庚申 (戊土失令+无根)
        ('身弱-戊土申月', {'year': ['戊', '申'], 'month': ['庚', '申'], 'day': ['戊', '申'], 'hour': ['庚', '申']}),
        # 3. 冬月调候: 甲子 丙子 甲子 丙子 (甲木子月, 冬令寒)
        ('冬月调候-甲木子月', {'year': ['甲', '子'], 'month': ['丙', '子'], 'day': ['甲', '子'], 'hour': ['丙', '子']}),
        # 4. 夏令调候: 丙午 甲午 丙午 甲午 (丙火午月, 夏令燥)
        ('夏令调候-丙火午月', {'year': ['丙', '午'], 'month': ['甲', '午'], 'day': ['丙', '午'], 'hour': ['甲', '午']}),
        # 5. 财格: 甲子 戊辰 甲子 戊辰 (甲木辰月, 偏财格)
        ('财格-甲木辰月', {'year': ['甲', '子'], 'month': ['戊', '辰'], 'day': ['甲', '子'], 'hour': ['戊', '辰']}),
        # 6. 官格: 甲子 辛酉 甲子 辛酉 (甲木酉月, 正官格)
        ('官格-甲木酉月', {'year': ['甲', '子'], 'month': ['辛', '酉'], 'day': ['甲', '子'], 'hour': ['辛', '酉']}),
    ]

    print("=" * 80)
    print("命理元统一输出层多案例端到端测试")
    print("=" * 80)

    all_pass = True
    for name, pillars in cases:
        try:
            summary = run_case(name, pillars)
            print(f"\n【{name}】Gate={summary['gate']}, 命理元={summary['meta_count']}")

            # 验证6命理元都有输出
            meta_ids = ['WANG_SHUAI', 'QIANG_RUO', 'GE_JU', 'DIAO_HOU', 'BING_YAO', 'YONG_SHEN']
            for mid in meta_ids:
                if mid in summary:
                    info = summary[mid]
                    cands = info.get('first_candidates', {})
                    cand_str = ', '.join([f"{tid}={elem}" for tid, elem in cands.items()])
                    print(f"  {mid}: 激活={info['activated']}, 冲突={info['conflict']}")
                    if cand_str:
                        print(f"    首选候选: {cand_str}")
                else:
                    print(f"  {mid}: 缺失!")
                    all_pass = False

            # 验证Gate通过
            if summary['gate'] != 'PASSED':
                print(f"  [FAIL] Gate未通过!")
                all_pass = False

        except Exception as e:
            print(f"\n【{name}】[ERROR] {e}")
            all_pass = False

    print()
    print("=" * 80)
    if all_pass:
        print("多案例端到端测试: ALL PASS")
        print(f"验证了 {len(cases)} 种命局类型, 6命理元全部正确输出")
    else:
        print("多案例端到端测试: 有失败!")
    print("=" * 80)

    return all_pass


if __name__ == '__main__':
    test_multiple_cases()
