# -*- coding: utf-8 -*-
"""V3.6.9㊻s115 断语生成层: 把 L0-L8 结构化字段串成分域成文断语(ch7 取象七原则 + ch14 断事以象定位).
四步: 取象(某字某宫某功, L4) → 定象(吉/凶/中性, L7 各域状态) → 应期(L8 大限/大运/流年) → 成文(分域断语).
ch7 七原则: ①某字在某宫做某功=定何事 ②定象=定方向 ③应期=定何时 ④成文=分域串断语.
本层只做"字段→断语"映射, 不发明新判据(所有断语消费已有 L0-L8 字段).
"""
from typing import Dict, List, Optional
from .blind_bazi_engine import BlindBaziResult
from .blind_yingqi import BlindYingqiEngine, YingqiResult

# ── 十神/干支/宫位中文对照 ─────────────────────────────────
_GAN_CN = {'JIA':'甲','YI':'乙','BING':'丙','DING':'丁','WU':'戊','JI':'己',
           'GENG':'庚','XIN':'辛','REN':'壬','GUI':'癸'}
_ZHI_CN = {'ZI':'子','CHOU':'丑','YIN':'寅','MAO':'卯','CHEN':'辰','SI':'巳',
           'WU':'午','WEI':'未','SHEN':'申','YOU':'酉','XU':'戌','HAI':'亥'}
_TG_CN = {'JIA':'甲','YI':'乙','BING':'丙','DING':'丁','WU':'戊','JI':'己',
          'GENG':'庚','XIN':'辛','REN':'壬','GUI':'癸','ZHOU':'丑'}
_POS_CN = {'year':'年','month':'月','day':'日','hour':'时','':''}

def _gz_cn(stem: str, branch: str) -> str:
    return f"{_GAN_CN.get(stem, stem)}{_ZHI_CN.get(branch, branch)}"

# ── 英文枚举 → 中文 干支 查表 (locate_event 输出 ganzhi=英文枚举如 RENZI) ──
_EN_TO_CN_GAN = {'J':'甲','Y':'乙','B':'丙','D':'丁','W':'戊','J':'己','G':'庚','X':'辛','R':'壬','G':'癸'}
# 干支 ganzhi 前6位英文枚举 → 中文: JIA甲 YI乙 BING丙 DING丁 WU戊 JI己 GENG庚 XIN辛 REN壬 GUI癸
def _ganzhi_en_to_cn(gz_en: str) -> str:
    """'RENZI' → '壬子', 'DINGCHOU' → '丁丑'. gz_en = 英文天干枚举+英文地支枚举(如 REN+ZI)."""
    _STEM_CN = {'JIA':'甲','YI':'乙','BING':'丙','DING':'丁','WU':'戊','JI':'己',
                'GENG':'庚','XIN':'辛','REN':'壬','GUI':'癸'}
    _BR_CN = {'ZI':'子','CHOU':'丑','YIN':'寅','MAO':'卯','CHEN':'辰','SI':'巳',
              'WU':'午','WEI':'未','SHEN':'申','YOU':'酉','XU':'戌','HAI':'亥'}
    # 天干=前3~4字符(枚举), 地支=剩余
    stem = gz_en[:4] if gz_en.startswith(('GENG','JIA','YI','BING','DING')) else gz_en[:3]
    # 简化: 逐干逐支匹配
    s_cn = ''
    for k, v in _STEM_CN.items():
        if gz_en.upper().startswith(k):
            s_cn = v
            break
    b_cn = ''
    for k, v in _BR_CN.items():
        if gz_en.upper().endswith(k):
            b_cn = v
            break
    return f"{s_cn}{b_cn}"

# ── L7 各域状态 → 断语方向/措辞 映射(ch 可核口径, 不发明新判据) ──
# 财域 (ch8 财命)
_WEALTH_DIR = {
    'PRESENT_ESTABLISHED': ('吉', '财星得地当令, 财缘厚'),
    'DIRECTED_ESTABLISHED': ('吉', '做功指向财且制得, 财可坐实'),
    'DIRECTED_AND_ESTABLISHED': ('吉', '主取宾取财路径成立, 财可坐实'),
    'DIRECTED_WITH_ROBBERY': ('吉带劫', '做功指向财但被比劫劫争, 财可得但被分/财来财去'),
    'SUBSTITUTED_AND_ESTABLISHED': ('吉', '以他物换象当财且坐实, 财可得(取财方式非直财)'),
    # ㊻s121 补漏: SUBSTITUTED_CANDIDATE 换象候选(效率 SMALL 未坐实, ch8 换象当财"虚象不作实断"),
    # 原 _WEALTH_DIR 缺此枚举 → 断语层 _dir_tuple 回落到 ('中性','财象未明') 但成文 f-string
    # 仍取 W[1] 为空(该枚举不在映射), 输出空句"财域 SUBSTITUTED_CANDIDATE(未明):。"
    'SUBSTITUTED_CANDIDATE': ('中性偏吉', '换象当财候选(食伤/官杀/禄代财, 效率未坐实), 财路隐伏非直财'),
    'SUBSTITUTED_ROBBED': ('凶', '换象当财被比劫夺走, 财路被截(贪污/破财)'),
    'PRESENT_ROBBED': ('凶', '财星在局被比劫夺走, 财不为我所有'),
    'ROBBED': ('凶', '财被劫, 求财费力/因人情破财'),
    'ABSENT': ('凶', '财星无做功无本, 财缘薄'),
    'UNDETERMINED': ('中性', '财象未明'),
}
# 官域 (ch9 官命)
_OFFICIAL_DIR = {
    'CONTROLLED_AND_CLEAN': ('吉', '官杀制得干净(金水伤官制净), 官权坐实/体制内'),
    'CONTROLLED_PARTIAL': ('吉带非', '官杀有制但不干净, 有官职但带官非口舌隐患'),
    'CONTROLLED': ('吉', '官杀被制, 有权(吉向)'),
    'DAMAGED': ('凶', '官星根受损, 官非/失权'),
    'ROBBED': ('凶', '官被比劫合走, 权非我所有'),
    'UNCONTROLLED': ('凶', '官杀无制(七杀无制), 犯官非/刑伤'),
    'LU_SUBSTITUTED': ('吉', '以禄代官(官禄格), 官贵以禄代位'),
    'UNDETERMINED': ('中性', '官象未明'),
}
# 婚域 (ch10 婚姻)
_MARRIAGE_DIR = {
    'HARMONIOUS': ('吉', '夫妻宫制去夫妻星的字=好婚姻(男比劫制财/女伤官制官)'),
    'CHALLENGED': ('中性偏凶', '婚姻受挑战(宫/星有伤但可经营), 婚动但可成'),
    'BROKEN': ('凶', '婚姻根本坏(夫宫被冲穿坏+夫星弱), 易婚变/离异/多婚'),
    'UNDETERMINED': ('中性', '婚姻象未明'),
}
# 子域 (ch4 L29 正官为女七杀为儿 + ch11)
_CHILD_DIR = {
    'POSITIVE': ('吉', '子女星有/子女宫得力, 有子且子女聪慧'),
    'CHALLENGED': ('中性', '子女有波折(印旺克食伤/子女宫被冲), 来得迟/管教严'),
    'ABSENT': ('凶', '子女缘薄(时支空/子女星无)'),
    'UNDETERMINED': ('中性', '子女象未明'),
}
# 牢域 (ch12)
_CRIME_DIR = {
    'RIBISHANG_GUAN': ('凶', '比劫伤官组合=拉帮结派(犯罪结构), 有牢狱/官非'),
    'QISHA_WUZHI': ('凶', '七杀无制化=犯罪结构, 犯法/刑伤'),
    'LU_GUAN_KONGDUI': ('凶', '禄与官杀对抗=犯罪, 官非'),
    'YIN_MIE_YANG': ('凶', '以阴灭阳(阴字坏阳用)=牢狱/重刑'),
    'FANJU_CHONGHE': ('凶', '反局+辰丑库=牢狱结构(反局主牢狱)'),
    'UNDETERMINED': ('中性', '无明确犯罪结构'),
}

def _dir_tuple(d: str, table: dict):
    """状态→(方向, 断语) 映射; 未收录枚举回落 (中性, 非空默认文案), 避免成文空句."""
    if d in table:
        return table[d]
    if not d or d == 'UNDETERMINED':
        return ('中性', '象未明(原局该域做功未坐实)')
    return ('未明', f'状态{d}(原局该域象未定, 不强行断)')


def generate_duanju(res: "BlindBaziResult",
                    yq: Optional[BlindYingqiEngine] = None,
                    birth: Optional[tuple] = None,
                    gender: str = "male",
                    year_range: Optional[tuple] = None,
                    top_n: int = 3) -> Dict[str, object]:
    """断语生成层入口: 输入 L0-L8 结构化字段, 输出分域成文断语.

    Args:
        res: BlindBaziEngine.compute_from_chart 的返回 (L0-L7 断事层)
        yq:  BlindYingqiEngine 实例 (供应期层, 可选; 传 birth+year_range 才出应期断语)
        birth: (y,m,d,h) 真实 solar 日期 (应期层需要)
        gender: male/female
        year_range: 应期扫描区间 (默认 birth[0] → birth[0]+60)
        top_n: 每域取 top N 应期年

    Returns:
        {"画像": [...], "断语": {"性格": str, "事业": str, "财": str, "婚": str,
         "子": str, "学": str, "健康": str, "牢狱": str, "应期节奏": str},
         "依据": {...每个断语对应的字段...}}
    """
    # ── ① 取象: 某字在某宫做某功 (L4) ──
    eff = [m for m, a in zip(res.zuo_gong_methods, res.zuo_gong_attributions)
           if a == "EFFECTIVE"]
    neg = [m for m, a in zip(res.zuo_gong_methods, res.zuo_gong_attributions)
           if a == "NEGATIVE"]
    # ── ② 定象: 各域状态 (L7) ──
    w_state = res.wealth_event_structure.get("wealth_state", "UNDETERMINED")
    o_state = res.official_event_structure.get("official_state", "UNDETERMINED")
    m_state = res.marriage_event_structure.get("marriage_state", "UNDETERMINED")
    ch_state = res.child_event_structure.get("child_state", "UNDETERMINED")
    c_state = res.crime_structure
    edu = res.education_level
    edu_field = res.education_field
    pers = res.day_master_personality

    W = _dir_tuple(w_state, _WEALTH_DIR)
    O = _dir_tuple(o_state, _OFFICIAL_DIR)
    M = _dir_tuple(m_state, _MARRIAGE_DIR)
    C = _dir_tuple(ch_state, _CHILD_DIR)
    CR = _dir_tuple(c_state, _CRIME_DIR)

    # ── ③ 应期 (L8, 可选) ──
    yingqi = {}
    if yq and birth:
        yr = year_range or (birth[0] + 1, birth[0] + 60)
        for dom in ["事业官贵", "财富", "婚姻口舌", "子女前程", "官贵刑伤"]:
            loc = yq.locate_event(birth, gender, domain=dom,
                                  year_range=yr, top_n=top_n)
            yingqi[dom] = [f"{x['year']}({_ganzhi_en_to_cn(x['ganzhi'])})"
                           for x in loc]

    # ── ④ 成文: 分域串断语 (ch7 取象 → ch14 断事以象定位) ──
    duanju: Dict[str, str] = {}

    # 性格 (ch14 日主性格 + ch4)
    pers_txt = pers if pers and pers != "UNDETERMINED" else "日主性格未明"
    duanju["性格"] = f"{pers_txt}。"

    # 事业 (ch9 官命 + ch8 财命, L7 官域 + L4 做功)
    off_evid = res.official_event_structure.get("reason", "")
    事业依据 = []
    if "伤官制官" in " ".join(eff) or "食伤制杀" in " ".join(eff):
        事业依据.append("伤官制官/食伤制杀=体制内实权")
    if "印化官杀" in " ".join(eff):
        事业依据.append("官配印=体制/单位文职")
    if "食伤生财" in " ".join(eff):
        事业依据.append("食伤生财=技艺/经商取财")
    if "比劫制财" in " ".join(neg):
        事业依据.append("比劫争财=合伙/夺权破财隐患")
    事业线 = "；".join(事业依据) if 事业依据 else "做功指向未明"
    duanju["事业"] = (f"官域 {o_state}（{O[0]}）：{O[1]}。{事业线}。"
                      f"宜行业：{edu_field if edu_field != 'UNDETERMINED' else '未明'}。")

    # 财 (ch8, L7 财域 + L4)
    duanju["财"] = f"财域 {w_state}（{W[0]}）：{W[1]}。"

    # 婚 (ch10, L7 婚域 + 宫/星/次数 + ch7 副宫)
    m_struct = res.marriage_event_structure
    宫 = _ZHI_CN.get(m_struct.get("spouse_palace", ""), m_struct.get("spouse_palace", ""))
    次数 = m_struct.get("marriage_count_signal", "")
    婚次数_txt = {"MULTIPLE": "多次婚源/易婚变", "SINGLE": "单一婚源", "": ""}.get(次数, "")
    副宫 = res.fugong_palace  # ch7 副宫(短暂婚姻/副职)
    副宫_txt = "，副宫多现(短暂婚姻/副职隐患)" if res.fugong_palace not in ("UNDETERMINED", "") else ""
    duanju["婚"] = (f"婚域 {m_state}（{M[0]}）：{M[1]}。"
                    f"夫宫={宫}，{婚次数_txt}{副宫_txt}。")

    # 子 (ch4/ch11, L7 子域)
    duanju["子"] = f"子域 {ch_state}（{C[0]}）：{C[1]}。"

    # 学 (ch11 ㊻s117: HIGHER_EDU/BASIC_EDU/NO_EDU 三档, 不精确到本科)
    _EDU_TXT = {
        'HIGHER_EDU': '高学历(学者型, 原书博士/硕士例)',
        'BASIC_EDU': '有学历(学业有成, 不精确到具体层级)',
        'NO_EDU': '无学历或学历不高(原书印不做功=不开化/伤官无制=聪明但学历低)',
    }
    edu_txt = _EDU_TXT.get(edu, '学历象未明')
    duanju["学"] = f"学历：{edu_txt}（{edu_field if edu_field != 'UNDETERMINED' else '学科未明'}）。"

    # 健康 (ch5 身体, L7 身域)
    b = res.body_event_candidate
    b_cand = b.get("candidate", "UNDETERMINED") if isinstance(b, dict) else str(b)
    duanju["健康"] = f"身域 {b_cand}：身体无重大刑伤信号。" if b_cand == "UNDETERMINED" else \
                     f"身域 {b_cand}（{b.get('body_part','')} 部位）：有刑伤/健康隐患。"

    # 牢狱 (ch12 + ㊻s117 crime_present 有无口径)
    crime_present = getattr(res, 'crime_present', None)  # ㊻s117 新增: 有无犯罪结构(布尔)
    if crime_present is None:
        crime_present = (c_state != "UNDETERMINED")
    if crime_present:
        duanju["牢狱"] = f"牢狱：有犯罪结构（{CR[1]}）→ 易犯官非/牢狱。"
    else:
        duanju["牢狱"] = f"牢狱：无明确犯罪结构（ch12四类犯罪结构未凑齐）→ 无牢狱象。"

    # 人际合伙 (ch6/ch8/ch12 + ㊻s119 interpersonal_structure 4 子维度)
    ip = getattr(res, 'interpersonal_structure', 'UNDETERMINED')
    _IP_TXT = {
        'BIXIONG': ('同伴反目', 'ch12比劫伤官=拉帮结派：合伙散伙/遭人出卖/利益分配翻脸'),
        'HEHUA_DECAI': ('合伙得财', 'ch8比劫当财=宾位制住同伙财归我：合作帮身成事(用劫富命)'),
        'FENLU_ZHENGDUI': ('利益争夺', 'ch6劫财=主位分禄破财：同辈争财/合伙争利被分'),
        'TONGPEI_STABLE': ('同辈平稳', 'ch6比肩/劫财在局无争夺/无反目：同辈缘分平稳'),
        'UNDETERMINED': ('人际未明', 'ch6无比劫/伤官做功：人际合伙象未明'),
    }
    ip_label, ip_desc = _IP_TXT.get(ip, ('人际未明', '人际合伙象未明'))
    duanju["人际合伙"] = f"人际：{ip_label}（{ip_desc}）。"

    # 名气口碑 (ch9 虚透=名气 + ch11 泄秀=成名 + ㊻s120 mingqi_structure)
    mq = getattr(res, 'mingqi_structure', 'UNDETERMINED')
    _MQ_TXT = {
        'XUTOU_MINGQU': ('有名气(虚名)', 'ch9官杀虚透=名气非实官(有虚名非实官)'),
        'XIUXIU_CHENGMING': ('秀气成名', 'ch11日主秀气泄秀=成名(得漂亮成名)'),
        'XINGZUO_DEJIANG': ('作品/得奖扬名', 'ch11食伤做功=有作品/技艺成名(得奖象)'),
        'UNDETERMINED': ('名气未明', 'ch9/ch11无名气做功象'),
    }
    mq_label, mq_desc = _MQ_TXT.get(mq, ('名气未明', ''))
    duanju["名气口碑"] = f"名气：{mq_label}（{mq_desc}）。"

    # 心性 (ch14 撤干神 ㊻s120 ㊻s121 通根虚实 + 日干象)
    xx = getattr(res, 'xingxing_cheganshen', 'UNDETERMINED')
    xx_evid = getattr(res, 'xingxing_evidence', [])
    xx_desc = (xx_evid[0] if xx_evid else '日干坐支五行同, 二象未分')
    duanju["心性"] = f"撤干神心性：{xx}。" if xx != 'UNDETERMINED' else f"撤干神心性：二象未分（{xx_desc}）。"

    # 福分寿元 (ch2 合寿/解合 + ch4 寿元星 + ㊻s120 fufen_structure)
    ff = getattr(res, 'fufen_structure', 'UNDETERMINED')
    _FF_TXT = {
        'SHOULD_YANHE': ('寿元有根', 'ch4食伤在局=寿元星有力(寿元有根/合寿延)'),
        'SHOUYUAN_XUEYUAN': ('寿元受损', 'ch4枭神夺食=夺寿元星(寿元受损/健康早夭隐患)'),
        'CAOLAO': ('操心劳碌', 'ch2正印为忌=操心劳碌(享福薄, 为别人操心)'),
        'UNDETERMINED': ('寿元未明', 'ch2/ch4寿元象未明'),
    }
    ff_label, ff_desc = _FF_TXT.get(ff, ('寿元未明', ''))
    duanju["福分寿元"] = f"福寿：{ff_label}（{ff_desc}）。"

    # 应期节奏 (ch2, L8)
    if yingqi:
        rhythm = []
        for dom, yrs in yingqi.items():
            if yrs:
                rhythm.append(f"{dom}动期 {'/'.join(yrs[:3])}")
        duanju["应期节奏"] = "；".join(rhythm) + "。"
    else:
        duanju["应期节奏"] = "（未传应期参数, 不出应期断语）"

    # ── 画像 (总体基调, ch13 一贵抵九贱 + ch1 势) ──
    shi = res.shi_direction
    fanguan = "反局" if res.zheng_fan_ju == "FAN_JU" else "正局"
    tone = res.tone_char
    画像 = [f"{fanguan}·{shi if shi != 'UNDETERMINED' else '势未明'}·基调字 {tone}"]
    # 核心断语一句话(取各域方向)
    dir_summary = []
    for label, (d, _) in [("事业", O), ("财", W), ("婚", M), ("子", C), ("牢", CR)]:
        if d not in ("中性", "未明"):
            dir_summary.append(f"{label}{d}")
    画像.append(" · ".join(dir_summary) if dir_summary else "各域中性")

    # ── 依据 (每断语消费的字段, 供核证) ──
    依据 = {
        "性格": {"field": "day_master_personality", "value": pers},
        "事业": {"field": "official_event_structure", "value": o_state,
                 "做功": eff, "负功": neg},
        "财": {"field": "wealth_event_structure", "value": w_state},
        "婚": {"field": "marriage_event_structure", "value": m_state,
               "宫": 宫, "次数": 次数},
        "子": {"field": "child_event_structure", "value": ch_state},
        "学": {"field": "education_level", "value": edu, "专业": edu_field,
               "判据": res.education_evidence[:2]},
        "健康": {"field": "body_event_candidate", "value": b_cand},
        "牢狱": {"field": "crime_structure", "value": c_state, "判据": res.crime_evidence},
        "应期": yingqi,
    }

    return {"画像": 画像, "断语": duanju, "依据": 依据}


def duanju_to_text(duj: Dict[str, object]) -> str:
    """断语 dict → 成文输出(可直接交付)."""
    lines = []
    lines.append("═══ 盲派断语 (ch7 取象七原则 + ch14 断事以象定位) ═══")
    lines.append(" ".join(duj.get("画像", [])))
    lines.append("")
    for k, v in (duj.get("断语") or {}).items():
        lines.append(f"  【{k}】{v}")
    return "\n".join(lines)
