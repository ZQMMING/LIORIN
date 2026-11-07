# -*- coding: utf-8 -*-
"""切片条件翻译验证器 (STEP-L7-2, 2026-10)
底层验证层: 病机已挂切片的 semantic 条件(自然语言) → 引擎谓词组合,
在六书案例上批量求值, 对照引擎病机触发, 输出:
  ① 映射矩阵(切片条件 vs 引擎触发)
  ② 错位发现(切片挂错方向: 触发/救应/应期)
  ③ 触发过宽/漏报信号(供"布尔程级/命中调节"矫正, 不焊死生产判定)

铁律: 切片先用 MD 验证; 条件翻译只作验证不作生产判定;
      无原文依据的映射标 UNVERIFIED, 不脑补.
"""
import glob
import importlib
import io
import json
import sys

sys.path.insert(0, '.')
importlib.invalidate_caches()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from p0_v2.bazi_gate import paipan

# ---------------------------------------------------------------- 谓词库
# 事实源: r['wuxing_power']['wuxing_power'][wx] = {combo,stem_n,ben_n,ju_n,banhe_n,ling_state}
#         r['root_weight_class_facts']  日主各支根
#         r['ge_cheng']                 ti_wx/xi_wx/ge

DANG_COMBO = 4   # 成党阈值(工程离散值, 与 engineering_assumptions 同源)


def _wpd(r):
    wp = r.get('wuxing_power') or {}
    return wp.get('wuxing_power', wp) if isinstance(wp, dict) else {}


def _combo(r, wx):
    """统一口径: 他干透干(排除日干) + 本气根 + 局票(ju*2+banhe*1), 与引擎 bing_debate._counts 同源."""
    from engines.common.bing_debate import _counts
    c = _counts(r.get('pillars') or {}, wx, r.get('transit_extra'))
    e = _wpd(r).get(wx) or {}
    try:
        ju = int(e.get('ju_n', 0) or 0) * 2 + int(e.get('banhe_n', 0) or 0) * 1
    except Exception:
        ju = 0
    return c['tou'] + c['ben'] + ju


def _ling(r, wx):
    return (_wpd(r).get(wx) or {}).get('ling_state', '')


def _dm(r):
    return r.get('daymaster_element', '')


def _dm_no_heavy(r):
    rw = r.get('root_weight_class_facts') or {}
    return not any(v.get('class') == 'HEAVY' for v in rw.values())


def _x_pressure_dm(r, wx):
    """wx 是否相对压过日主(辩层偏序键): 返回 True 表示 wx 更旺."""
    from engines.common.bing_debate import _counts, _dang_level, month_order
    pl = r.get('pillars') or {}
    dm = _dm(r)
    m = r.get('month_qi_element', '')
    cx = _counts(pl, wx, r.get('transit_extra'))
    cd = _counts(pl, dm, r.get('transit_extra'))
    kx = (month_order(wx, m) if m else 9, _dang_level(cx['tou'] + cx['ben']), -cx['tou'], -cx['ben'])
    kd = (month_order(dm, m) if m else 9, _dang_level(cd['tou'] + cd['ben']), -cd['tou'], -cd['ben'])
    return kx < kd


# ---------------------------------------------------------------- 谓词表达式
# 口径对齐(防搞偏): dang_ling 与引擎 bingyao._kexie_trigger 的 dangling 完全一致
#   = (month_qi_element == wx), 即「月令本气即该五行」; 不含 '相'(月令所生,
#   引擎不当令, 若算入会把杀重/财多的"仅谓词"虚高成漏报信号)。
PRED = {
    'combo_ge4':    lambda r, wx: _combo(r, wx) >= DANG_COMBO,
    'dang_ling':    lambda r, wx: (r.get('month_qi_element') or '') == wx,
    'tou_ge1':      lambda r, wx: _counts_tou(r, wx) >= 1,
    'ben_ge1':      lambda r, wx: _counts_ben(r, wx) >= 1,
    'dm_no_heavy':  lambda r, wx: _dm_no_heavy(r),
    'x_pressure':   lambda r, wx: _x_pressure_dm(r, wx),
}


def _gate_reason(r, wx):
    """引擎对病五行 wx 的附加闸门(对齐 bingyao_layer 过滤逻辑):
    返回 None=无闸门(谓词命中却未触发 → 真漏报信号); 否则为闸门名列表."""
    gc = r.get('ge_cheng') or {}
    ti = gc.get('ti_wx') or []
    xi = gc.get('xi_wx') or []
    zhi = gc.get('zhi_wx') or []
    hua = gc.get('hua_wx') or []
    KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
    WO_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    reasons = []
    if wx in ti:
        reasons.append('ti_wx格体豁免')
    if wx in xi:
        reasons.append('xi_wx喜神豁免')
    if any(KE.get(z) == wx for z in zhi):
        reasons.append('zhi_wx制化过滤')
    if any(WO_SHENG.get(wx) == h for h in hua):
        reasons.append('hua_wx化泄过滤')
    # 引擎内部闸门(病药层 _kexie_trigger/制化闸门, 非格局层输出):
    #   ① 杀重身轻: 食神透(tou>=1)或印透 → 有制化不报
    #   ② 泄气太重: 印透制食伤 → 不报
    dm = _dm(r)
    from engines.common.bing_debate import _counts
    pl = r.get('pillars') or {}
    shi_wx = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}.get(dm, '')
    yin_wx = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}.get(dm, '')
    if _counts(pl, shi_wx, r.get('transit_extra'))['tou'] >= 1:
        reasons.append('引擎食神透制(内部闸门)')
    if _counts(pl, yin_wx, r.get('transit_extra'))['tou'] >= 1:
        reasons.append('引擎印透化(内部闸门)')
    return reasons or None


def _counts_tou(r, wx):
    from engines.common.bing_debate import _counts
    return _counts(r.get('pillars') or {}, wx, r.get('transit_extra'))['tou']


def _counts_ben(r, wx):
    from engines.common.bing_debate import _counts
    return _counts(r.get('pillars') or {}, wx, r.get('transit_extra'))['ben']

# ---------------------------------------------------------------- 病机切片条件映射
# 每条: (病机ID, 切片ID, 切片类型[触发/救应/应期/总纲], 谓词表达式, 映射状态)
# 表达式: (wx,) -> [谓词名...], AND 组合; 多组为 OR(任一组成立即命中)
SLICE_MAP = [
    ('CAI_DUO_SHEN_RUO', 'PATHOLOGY.QIANG_RUO.004', '触发',
     [['dang_ling', 'dm_no_heavy'], ['combo_ge4', 'dm_no_heavy']], '已校准L7-1'),
    ('SHA_ZHONG_SHEN_QING', 'PATHOLOGY.QIANG_RUO.005', '触发',
     [['dang_ling', 'dm_no_heavy'], ['combo_ge4', 'dm_no_heavy']], 'OK'),
    ('XIE_QI_TAI_ZHONG', 'PATHOLOGY.QIANG_RUO.020', '总纲(旺病四类)',
     [['dang_ling', 'dm_no_heavy'], ['combo_ge4', 'dm_no_heavy']],
     '切片归属待核: 020为旺病总纲, 泄气病无专条'),
    ('BIJIE_CHENG_DANG', 'PATHOLOGY.QIANG_RUO.001', '总纲(众寡)',
     [['combo_ge4']], '总纲为最高准神: 比劫成党=日主同类combo>=4(众); x_pressure自比日主为bug已删'),
    ('SHANGGUAN_JIAN_GUAN', 'STRUCTURE.GE_JU.JIU_YING.003', '救应(化解)',
     [], '错位登记: 该切片为救应条件非触发; 触发切片(YHZP伤官见官为祸)缺'),
    ('XIAO_DUO_SHI', 'PATHOLOGY.JIE_GOU.018', '应期(岁运)',
     [], '错位登记: 该切片为岁运应期非原局触发; 触发切片缺'),
    ('YIN_DUO_MAI_ZI', 'STATE.WANG_SHUAI.FAN_JU.001', '触发(反局总纲)',
     [['combo_ge4', 'dm_no_heavy'], ['dang_ling', 'dm_no_heavy']],
     'OK: 印成党/当令埋日主(土重金埋同构); 补当令组对齐引擎触发'),
    ('ZHI_SHA_TAI_GUO', 'SUI_YUN.RE_EVALUATION.DA_YUN_ZHI_YU.009', '命例(旁参)',
     [['combo_ge4', 'dm_no_heavy']], '旁参: 唯一提制伏太过之切片, 为命例非通则'),
]


def _eval_expr(r, wx, groups):
    """谓词表达式求值: 组内 AND, 组间 OR."""
    if not groups:
        return None   # 无谓词(错位/缺切片)
    for g in groups:
        if all(PRED[p](r, wx) for p in g):
            return True
    return False


# ---------------------------------------------------------------- 批量求值
def run(books=None, limit=None):
    fps = sorted(glob.glob('p0_v2/case_audit/*_clean.jsonl'))
    stat = {}   # bing_id -> {trig/pred/both/pred_only/trig_only/none + gated/ungated 样本}
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
            trig_ids = {b.get('bing_id') for b in (r.get('bing_list') or [])}
            for bid, sid, stype, groups, status in SLICE_MAP:
                s = stat.setdefault(bid, {'trig': 0, 'pred': 0, 'both': 0, 'pred_only': 0,
                                          'trig_only': 0, 'none': 0, 'gated': 0, 'ungated': 0,
                                          'samples': []})
                role_wx = {
                    'CAI_DUO_SHEN_RUO': '财', 'SHA_ZHONG_SHEN_QING': '官杀',
                    'XIE_QI_TAI_ZHONG': '食伤', 'BIJIE_CHENG_DANG': '比劫',
                    'SHANGGUAN_JIAN_GUAN': '官杀', 'XIAO_DUO_SHI': '印枭',
                    'YIN_DUO_MAI_ZI': '印枭', 'ZHI_SHA_TAI_GUO': '食伤',
                }
                from engines.common.bing_debate import role_to_wx
                # 病机五行: 优先取引擎已挂的 bing_wx(同源防偏), 未触发时用角色推算
                _ewx = next((b.get('bing_wx') for b in (r.get('bing_list') or [])
                             if b.get('bing_id') == bid and b.get('bing_wx')), None)
                wx = _ewx or role_to_wx(role_wx.get(bid, ''), _dm(r))
                ph = _eval_expr(r, wx, groups)
                trig = bid in trig_ids
                if trig and ph:
                    s['both'] += 1
                elif trig:
                    s['trig_only'] += 1
                    if len(s['samples']) < 5:
                        s['samples'].append(('T', d.get('case_id'), d.get('bazi'),
                                             (d.get('analysis') or '')[:50], wx))
                elif ph:
                    s['pred_only'] += 1
                    # 闸门标注: 谓词命中但引擎未触发 —— 是闸门所致还是真漏报
                    gr = _gate_reason(r, wx)
                    if gr:
                        s['gated'] += 1
                    else:
                        s['ungated'] += 1
                        if len(s['samples']) < 5:
                            s['samples'].append(('U', d.get('case_id'), d.get('bazi'),
                                                 (d.get('analysis') or '')[:50], wx))
                else:
                    s['none'] += 1
                s['trig'] += int(trig)
                s['pred'] += int(bool(ph))

    print('%-20s %5s %5s %5s %7s %7s %8s  %s' % ('病机', '触发', '谓词', '双中', '仅触发', '仅谓词', '双否', '切片'))
    for bid, sid, stype, groups, status in SLICE_MAP:
        s = stat.get(bid, {})
        gate_note = ''
        if s.get('pred_only'):
            gate_note = '  [仅谓词: 闸门%d 无闸门%d]' % (s.get('gated', 0), s.get('ungated', 0))
        print('%-20s %5d %5d %5d %7d %7d %8d  %s[%s] %s%s'
              % (bid, s.get('trig', 0), s.get('pred', 0), s.get('both', 0),
                 s.get('trig_only', 0), s.get('pred_only', 0), s.get('none', 0),
                 stype, sid.split('.')[-1], status, gate_note))
    print()
    print('== 无闸门仅谓词(真漏报信号) 与 仅触发(过宽信号) 抽样 ==')
    for bid, sid, stype, groups, status in SLICE_MAP:
        s = stat.get(bid, {})
        for tag, cid, bz, txt, wx in s.get('samples', []):
            print('  [%s] %-18s %-8s %s  %s' % (tag, bid, cid, bz, txt))


def selfcheck(bazi):
    """人工核对: 打印单盘全部病机谓词明细, 与引擎触发/闸门对照."""
    importlib.invalidate_caches()
    r = paipan(bazi)
    trig_ids = {b.get('bing_id') for b in (r.get('bing_list') or [])}
    gc = r.get('ge_cheng') or {}
    print('盘: %s  月令本气=%s 日主=%s' % (bazi, r.get('month_qi_element'), _dm(r)))
    print('格: %s  ti_wx=%s xi_wx=%s zhi_wx=%s hua_wx=%s' % (gc.get('ge'), gc.get('ti_wx'),
          gc.get('xi_wx'), gc.get('zhi_wx'), gc.get('hua_wx')))
    print('引擎病机: %s' % [(b.get('bing_id'), b.get('bing_wx'), b.get('severity'))
                          for b in (r.get('bing_list') or [])])
    for bid, sid, stype, groups, status in SLICE_MAP:
        role_wx = {'CAI_DUO_SHEN_RUO': '财', 'SHA_ZHONG_SHEN_QING': '官杀',
                   'XIE_QI_TAI_ZHONG': '食伤', 'BIJIE_CHENG_DANG': '比劫',
                   'SHANGGUAN_JIAN_GUAN': '官杀', 'XIAO_DUO_SHI': '印枭',
                   'YIN_DUO_MAI_ZI': '印枭', 'ZHI_SHA_TAI_GUO': '食伤'}
        from engines.common.bing_debate import role_to_wx
        wx = role_to_wx(role_wx.get(bid, ''), _dm(r))
        ph = _eval_expr(r, wx, groups)
        trig = bid in trig_ids
        gr = _gate_reason(r, wx)
        print('  %-20s wx=%-2s 谓词=%-5s 引擎=%-5s 闸门=%s'
              % (bid, wx, 'T' if ph else 'F', 'T' if trig else 'F', gr or '-'))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--books', nargs='*', default=None)
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--selfcheck', type=str, default=None, help='单盘人工核对(四柱)')
    a = ap.parse_args()
    if a.selfcheck:
        selfcheck(a.selfcheck)
    else:
        run(books=a.books, limit=a.limit)
