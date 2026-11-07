# -*- coding: utf-8 -*-
"""v1.7 病药分域: 标记识别 + 主语定位 + 域归属判定.

补《案例执行方案》§4.2 标准化表未实现的句式("以X…为用/取X为用/X为病/X为药/X为救应"),
且每条提取强制带域归属, 避免补召回的案例变成新的跨域污染源.

域定义(v1.7 §0.3 五域):
  GEJU    格局病域  成格之神/破格之神   <- 只有这个域是 PZZQ 格局层的对标样本
  WANGSH  旺衰病域  扶抑药(帮身/扶身/生扶)
  JIEGOU  结构病域  制化药(制/化/合解/去留)
  QIHOU   气候病域  调候药(寒暖燥湿)
  WUXING  五行病域  通关药/流通药
  UNKNOWN 未定     判不出就留 UNKNOWN, 不进任何域桶(宁漏勿错, 规范铁律3)

设计要点(修 v1 版的四处缺陷):
 1. 主语位置随标记类型走: BEFORE(…主语为用) / INSIDE(以主语…为用) / AFTER(宜用主语)
 2. 域线索只看 marker 所在的逗号/分号小节, 不看全句(避免同句前半污染)
 3. 药名强信号(调候/通关/扶身/制/化/救应…)优先于语境线索
 4. 人事/纪年噪声词过滤("未贵直接为用"里的"未"不是用神)
"""
import re

GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
WUX = '木火土金水'
SHISHEN = ('正官', '七杀', '偏官', '正印', '偏印', '正财', '偏财',
           '食神', '伤官', '比肩', '劫财')
SHORT = {'官': '正官', '杀': '七杀', '印': '正印', '枭': '偏印', '财': '财',
         '食': '食神', '伤': '伤官', '比': '比肩', '劫': '劫财'}
TG_CANON = {w: w for w in SHISHEN}
TG_CANON.update(SHORT)

# ---------- 主语候选: 长词优先 ----------
SUBJ = ([(w, 'SHISHEN:' + w) for w in SHISHEN] +
        [(w, 'SHISHEN:' + SHORT[w]) for w in SHORT] +
        [(w, 'GAN:' + w) for w in GAN] +
        [(w, 'ZHI:' + w) for w in ZHI] +
        [(w, 'WX:' + w) for w in WUX])
SUBJ.sort(key=lambda x: -len(x[0]))

# ---------- 人事/纪年噪声: 这些字是贵人/荫/祖基等, 不是用神 ----------
NOISE = re.compile(r'贵人为用|未贵|己贵|癸贵|丁贵|祖基|遗荫|提携|荫|直接为用|'
                   r'本身|名誉|科名|荫���|受贵|之贵|显贵|荣华')

# ---------- 域判定信号 ----------
# GRID_STRONG 决定性格域信号: 出现即表明原文在论"格"的成败, 优先级高于任何药名.
#   注意: "月令"单用【不是】格域信号 —— PZZQ 里"月令X"只是主语结构,
#   如"月令偏财…调候为急"是调候域, "月令七煞透干"才是定格语境. 故月令只作 WEAK 复合.
GRID_STRONG = re.compile(
    r'成格|破格|成中有败|败中有成|格体|救应|两气成象|化(?:土|金|水|木|火)格|'
    r'财格|官格|印格|食(?:神)?格|伤官格|七杀格|煞格|正官格|建禄|月劫|阳刃|'
    r'专旺|曲直|炎上|稼穑|从革|润下|'
    r'从格|从杀|从财|从儿|从官|从势|弃命|见论[^。]{1,8}篇')
# 月令 + 十神 = 定格(弱, 让位于药名信号)
GRID_WEAK = re.compile(r'月令[^。；]{0,6}(?:七杀|煞|财|官|印|食|伤)')

YAO_DOMAIN = [
    ('QIHOU', re.compile(r'调候|寒暖|寒(?:木|局|月|冷|凝|水)|暖局|解冻|寒木向阳|'
                        r'润燥|炎(?:上|燥)|燥(?:土|热|金|烈)|湿(?:土|冷)?|'
                        r'需[火水]|火暖|水润|调和气候|土燥|金寒水冷|火炎土燥|为急')),
    ('WUXING', re.compile(r'通关|流通|源流|归路|通关之神|两行相战')),
    ('WANGSH', re.compile(r'帮身|扶身|扶抑|生扶|抑之|扶之|抑制|任财|任官|担得起|'
                          r'用比劫|用劫财|帮(?:日主|我)|身(?:弱|强|轻)(?:不|而|则)|'
                          r'扶助日元|不用官')),
    ('JIEGOU', re.compile(r'制(?:煞|杀|伤官|官|印|之)|化(?:煞|杀|印|官|之)|'
                          r'合解|去留|取清|去官留杀|去煞留官|合化|解合')),
]
# 语境线索(弱, 仅在小节无药名信号时用)
# 语境线索(弱, 仅在小节无药名/格域信号时用)
# GEJU 线索与 GRID_STRONG 对齐: 不含"月令"(主语结构)与"贵"(人事情境, 会误命中
# "月令偏财当令, 比劫争财为病"这类旺衰/结构域表述)
CUE = [
    ('QIHOU', re.compile(r'寒|暖|燥|湿|调候|火炎|水冷')),
    ('WUXING', re.compile(r'通关|流通|源流|相战')),
    ('WANGSH', re.compile(r'身弱|身强|身轻|帮身|扶身|任财|任官|担不起')),
    ('JIEGOU', re.compile(r'制[煞杀伤官印之]|化[煞杀印官之]|合解|去留|取清')),
    ('GEJU', re.compile(r'成格|破格|格体|救应|定格|格局')),
]

# ---------- 标记: (正则, 极性, 主语位置, 组号) ----------
#   BEFORE: 主语在 match 之前(尾标式)  INSIDE: 主语在 m.group(n) 里  AFTER: 主语在 match 之后
MARKERS = [
    (r'(?:以|取|乃用|得|取年上|取时上)?([^，。；、]{0,6}?)为救应(?:之神)?', '喜', 'INSIDE', 1),
    (r'为用神', '喜', 'BEFORE', 0),
    (r'为用', '喜', 'BEFORE', 0),
    (r'为喜(?:神)?', '喜', 'BEFORE', 0),
    (r'宜用([^，。；、]{1,3})', '喜', 'INSIDE', 1),
    (r'为病(?:神)?', '忌', 'BEFORE', 0),
    (r'为药', '喜', 'BEFORE', 0),
    (r'为忌(?:神)?|所忌|俱为所忌', '忌', 'BEFORE', 0),
    (r'([^，。；、]{1,3})为用神', '喜', 'INSIDE', 1),
    (r'([^，。；、]{1,3})为用', '喜', 'INSIDE', 1),
]


def _seg_of(clause, pos):
    """取 marker 所在的小节(逗号/分号/顿号切分), 避免同句他段污染域判定"""
    seps = '，。；、,;'
    a = pos
    while a > 0 and clause[a - 1] not in seps:
        a -= 1
    b = pos
    while b < len(clause) and clause[b] not in seps:
        b += 1
    return clause[a:b]


def _pick(seg, after_prefix=None):
    """从小节里挑主语: 长词优先, 同长度取靠后者.
    after_prefix 给定时(已剥掉"以/取"等介词), 取【位置最靠前】的 token,
    对应中文"以[药][动作]为用"结构 —— 药紧跟介词, 动作在中间不可当主语
    ("以庚劈甲引丁为用" 主语是庚, 不是位置更靠后的甲/丁)."""
    if after_prefix:
        best = None
        for word, kind in SUBJ:
            i = after_prefix.find(word)
            if i < 0:
                continue
            cand = (i, -len(word), word, kind)
            if best is None or cand[:2] < best[:2]:
                best = cand
        return (best[2], best[3]) if best else None
    best = None
    for word, kind in SUBJ:
        i = seg.rfind(word)
        if i < 0:
            continue
        cand = (len(word), i, word, kind)
        if best is None or (cand[0], cand[1]) > (best[0], best[1]):
            best = cand
    return (best[2], best[3]) if best else None


def _classify(seg, extra='', prev=''):
    """域判定优先级:
      1. 决定性格域信号(成格/破格/格名/救应/从格) —— 原文在论"格", 压过任何药名
      2. 当前小节药名(调候/通关/帮身/制化)
      3. 后一小节药名(因果后置: "取午火为用, 乃调和气候之意")
      4. 月令+十神 复合(弱格域信号)
      5. 前后小节语境线索
      6. UNKNOWN(宁漏勿错, 规范铁律3 —— 判不出就不进任何域桶)
    """
    pool = seg + ' ' + extra
    if GRID_STRONG.search(pool):
        return 'GEJU', 'grid_strong'
    for dom, rx in YAO_DOMAIN:
        if rx.search(seg):
            return dom, 'yao:' + dom
    for dom, rx in YAO_DOMAIN:
        if rx.search(extra):
            return dom, 'yao_next:' + dom
    if GRID_WEAK.search(pool) and not YAO_DOMAIN[0][1].search(pool):
        return 'GEJU', 'grid_weak(月令+十神)'
    for dom, rx in CUE:
        if rx.search(pool):
            return dom, 'cue:' + dom
    for dom, rx in CUE:
        if rx.search(prev):
            return dom, 'cue_prev:' + dom
    return 'UNKNOWN', 'unresolved'


def extract_marked(clause):
    """单个原文句 -> [{subj, kind, polarity, domain, domain_src, marker, seg}]
    先按 逗号/分号/顿号 切小节, 每小节只取首个 marker:
      - 一句通常只讲一个用神(小节级单位), 避免 BEFORE/INSIDE 双命中重复
      - 天然支持同句多义("以丁为用神, 壬水为病, 己土制壬水为药" -> 三小节三结果)
    """
    seps = '，。；、,;'
    out = []
    # 切成小节, 保留下一小节尾巴供域判定(因果常后置)
    segs, cur = [], ''
    for ch in clause:
        if ch in seps:
            if cur:
                segs.append(cur)
            cur = ''
        else:
            cur += ch
    if cur:
        segs.append(cur)

    for i, seg in enumerate(segs):
        if NOISE.search(seg):
            continue
        nxt = segs[i + 1] if i + 1 < len(segs) else ''
        prv = segs[i - 1] if i > 0 else ''
        got = None
        for pat, pol, pos, grp in MARKERS:
            m = re.search(pat, seg)
            if not m:
                continue
            if pos == 'INSIDE':
                raw = (m.group(grp) or '')
                if len(raw) > 6:
                    continue
                stripped = re.sub(r'^(?:以|取|用|得|另|即)', '', raw)
                p = _pick(stripped, after_prefix=stripped)
                use_seg = stripped
            else:
                # "以/取[药][动作]为用": 剥到介词, 主语取其后紧邻 token(否则会取到动作词"制伤/引丁")
                # 介词表不可含 "用" —— "化煞**为用**" 的"用"不是介词, 会把主语"庚印"剥掉
                head = re.sub(r'^.*?(?:以|取|宜)', '', seg, count=1) \
                    if re.search(r'(?:以|取|宜)', seg) else seg
                p = _pick(head, after_prefix=head) or _pick(seg)
                use_seg = seg
            if not p:
                continue
            word, kind = p
            if NOISE.search(use_seg):
                continue
            dom, dsrc = _classify(use_seg, m.group() + ' ' + nxt, prv)
            got = {'subj': word, 'kind': kind, 'polarity': pol,
                   'domain': dom, 'domain_src': dsrc,
                   'marker': m.group()[:12], 'seg': use_seg[:40]}
            break
        if got:
            out.append(got)
    return out
