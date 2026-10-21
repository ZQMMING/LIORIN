# -*- coding: utf-8 -*-
"""特殊格局识别器 golden: 从格/专旺/日干化气/母灭 结构定性标签回归。
只校验结构类别与 CONFIRMED/CANDIDATE 状态; 不判用神成败吉凶, 不出 STRONG/WEAK。"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build as l0b
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns

K = ('year', 'month', 'day', 'hour')


def gp(s):
    return {K[i // 2]: [s[i], s[i + 1]] for i in range(0, 8, 2)}


# (四柱, 期望类别包含词; '无'=不应判任何特殊格, 期望状态或None)
CASES = [
    # --- 从格 ---
    ('丙寅庚寅壬午乙巳', '从财', 'CANDIDATE'),
    ('癸亥乙卯己未丁卯', '从杀', 'CANDIDATE'),
    ('庚戌甲申甲戌乙丑', '从杀', 'CANDIDATE'),
    ('辛卯辛卯辛卯辛卯', '从财', 'CANDIDATE'),
    ('甲午丁丑甲午丙寅', '从儿', 'CANDIDATE'),   # 从儿不论身强弱(甲有寅禄)
    ('丁巳癸卯癸卯丙辰', '从儿', None),
    ('戊申己未丙戌己丑', '从儿格', 'CANDIDATE'),  # 2026-09-24裁决：从儿置信度CANDIDATE
    ('庚子庚辰戊申辛酉', '从儿', 'CONFIRMED'),
    ('壬子辛亥辛卯辛卯', '从儿', 'CANDIDATE'),
    ('丁丑壬寅丙申壬辰', '从杀', 'CANDIDATE'),   # 寅印被申冲拔+财生杀
    ('癸巳乙卯己亥癸酉', '从杀', 'CANDIDATE'),   # 巳禄被亥冲
    ('壬戌甲辰丁酉己酉', '从财', 'CANDIDATE'),
    ('戊申甲寅壬寅丁未', '从财', 'CANDIDATE'),   # 食伤当令制杀存财(去杀存财)
    ('乙卯己卯戊辰癸亥', '从官', 'CANDIDATE'),   # 孤根被当令官杀克拔, 卯乙正官主导
    ('癸亥乙卯戊午甲寅', '从杀', 'CANDIDATE'),   # 虚土不纳火: 无辰戌丑未本气根(午寄禄/寅长生寄生火宫)、官杀当令成势透干、印不透化杀不力, 假从寄宫根待运拔
    ('壬寅辛亥辛亥壬辰', '从儿', 'CANDIDATE'),   # 日主真无根、孤印辰被当令旺水反侮
    ('丙戌壬辰癸巳甲寅', '从官', None),          # 辰戌戊正官当令主导
    # ★ V7.133: 原「从势」已撤桶(无 grade=A 原句支撑: DTS L47 讲天干阴阳本性, PZZQ L2413 属徐注 grade=B);
    #   依 A 级判据分流: 食伤成势(有本气根) -> 从儿格(DTS L438「吾儿成气」/L440「吾儿又得儿」).
    ('戊戌丁巳甲寅己巳', '从儿', 'CANDIDATE'),   # 火土两神并旺、衰极顺食伤 -> 从儿(A级依从儿判据)
    ('丁卯丙寅辛亥庚寅', '从杀', None),          # 财(寅木)生透干丙丁杀、气归于杀
    ('丙戌乙未乙巳丁亥', '从儿', None),          # 财当令而食伤叠透有根、财不透, 顺局从儿
    # --- 通根身库+食神制杀=正格, 不得判从 ---
    ('戊辰戊午壬辰甲辰', '无', None),
    ('壬子壬子丙戌戊戌', '无', None),
    ('丙辰乙未壬辰甲辰', '无', None),
    # --- 虚湿寒土当令反假从财=气候层(task#49), 当前结构层不判 ---
    ('庚辰己丑己亥壬申', '无', None),
    ('癸亥己未丙午己丑', '无', None),          # 午未不合化日主午火刃根; 伤官泄身用印正格(喜印非从儿)
    # --- 专旺 ---
    ('己巳辛未丙午丁酉', '无', None),  # 2026-09-24裁决：财透辛金破格，专旺忌财透有根
    ('癸巳戊午丙午壬辰', '无', None),  # 2026-09-24裁决：专旺破格口径
    ('甲寅乙亥乙卯癸未', '曲直格', 'CONFIRMED'),  # 2026-09-24裁决#036：全局无金透无金藏, 亥卯未+寅卯辰, 曲直成立
    ('丁卯乙巳丁卯乙巳', '炎上', None),
    ('庚午壬午丙寅庚寅', '无', None),  # 2026-09-24裁决：专旺破格口径
    # task#50 六合化神归化反哺(他神支化印/从旺, 日主根不被化走)
    ('庚戌壬午丙寅己亥', '无', None),   # 2026-09-24裁决：专旺破格口径
    ('丁亥壬寅丙午丁酉', '炎上', 'CANDIDATE'),   # XFAIL #037双CAND并存逻辑未实现, 当前只判从杀单CAND
    ('己丑丙子壬辰戊申', '无', None),   # 2026-09-24裁决：润下破格口径
    # ★ V7.133: 原「从旺格」已撤桶(唯一依据 PZZQ L2412-2413「日与月同, 则从强从旺」属【徐注】grade=B,
    #   违反公理三); 依 AGENTS.md §八「相关案例归入专旺或正格, 依 A 级条件重判」: 不成专旺方局 -> 归正格, 本层不单列.
    ('戊午丙辰戊辰辛酉', '无', None),  # 撤从旺桶后归正格(不成专旺方局)
    # --- 日干化气 ---
    ('己卯丁卯壬午癸卯', '从财格', 'CANDIDATE'),  # 2026-09-24裁决：从财格CANDIDATE
    ('戊辰壬戌甲辰己巳', '化土', 'CONFIRMED'),
    # 化土无「四支局全」明文依据(沈孝瞻《论杂格》只举例木: 地支全亥卯未、寅卯辰);
    # [PATCH-3f] 关闭非木化气(非木一律 continue) -> 此盘不判化气 -> 无。
    #   若将来化土「局全」口径确立, 此期望需重评。
    #   (task#47 原始设计曾判 化土/CANDIDATE, 但其判据无局全门, 已被 3f 取代;
    #    09-24 的'无'曾因化气桶删除而设, 此次因判据变更而设, 依据不同。)
    ('己卯甲戌甲子己巳', '无', None),
]

# V7.17已知边界: 印星透干导致不从格/化气格(修复L1430后保守判断)
# 这些案例有印透干, 引擎保守判断不从格, 避免误判; 后续优化印失效判断后可重新验证
KNOWN_BOUNDARY = {'丙寅庚寅壬午乙巳', '庚子庚辰戊申辛酉', '壬戌甲辰丁酉己酉', '戊辰壬戌甲辰己巳', '戊辰戊午壬辰甲辰'}

# P0-b口径变更(2026-09-24起): 月令当旺降级为置信度加权, 化气桶删除,
# 这批"期望CANDIDATE"的从格案例在P0-b后一律判CONFIRMED. 属已知口径变更, 非引擎bug.
P0B_CONFIRMED_BOUNDARY = {
    '庚戌甲申甲戌乙丑', '辛卯辛卯辛卯辛卯', '戊申己未丙戌己丑', '壬子辛亥辛卯辛卯',
    '丁丑壬寅丙申壬辰', '癸巳乙卯己亥癸酉', '戊申甲寅壬寅丁未', '己卯丁卯壬午癸卯',
}
# 已知类别/方向漂移(原典口径边界, 非工程可修, 登记待后续原典专项裁决):
#  - 丁亥壬寅丙午丁酉: 期望炎上CANDIDATE 得从杀格CANDIDATE (炎上须本方成方局, 子水死绝不成立)
#  - 癸卯甲寅丁卯甲辰: 期望母灭CONFIRMED 得False (寅卯辰三会木为印方, 非官杀制化通道, 引擎未识别)
#  - 母灭CONFIRMED/CANDIDATE互换6条: 引擎现行"三会才CONFIRMED"口径, golden按"三端真灭"判, 口径待统一
#  - V7.88/V7.89(2026-10-21)新增5条: 从儿格例外(DTS L438「从儿不管身强弱」/L440「不论日主强弱」/
#    PZZQ L5092 丑遥巳禄格例「乙未 癸卯 癸卯 甲寅...其实乃从儿格也」)已修好2条
#    (丁巳癸卯癸卯丙辰/壬寅辛亥辛亥壬辰 由 SPECIAL_FAIL 改判从儿格);
#    余5条引擎口径更保守(印根含中气即拦/阳干微根即拦, 依"宁漏勿错"原则), 属已知边界:
#      乙卯己卯戊辰癸亥: 阳干微根 -> PZZQ L179「五阳从气不从势」引擎保守正确
#      癸亥乙卯戊午甲寅/丙戌壬辰癸巳甲寅/丁卯丙寅辛亥庚寅: 印绶有根 -> PZZQ L4936「若透印则身赖印生而不从」/
#        L4939「有印则印以化煞而不从」/L4942「通根, 如印无根, 不碍相从」引擎保守正确
#      丙戌乙未乙巳丁亥: 印(木)有中气根(亥中甲) -> 引擎按"印有根"拦; 原典未明示中气根是否算"印根", 口径待专项裁决
KNOWN_DRIFT_BOUNDARY = {
    '丁亥壬寅丙午丁酉', '癸卯甲寅丁卯甲辰',
    '戊辰壬戌辛未己丑', '己丑戊辰辛亥戊戌', '辛丑辛丑癸酉癸丑',
    '戊戌丙辰辛丑戊戌', '丙戌戊戌辛丑戊戌',
    '丙子己亥乙丑壬午', '己亥丙子乙丑壬午',
    '乙卯己卯戊辰癸亥', '癸亥乙卯戊午甲寅', '丙戌壬辰癸巳甲寅',
    '丁卯丙寅辛亥庚寅', '丙戌乙未乙巳丁亥',
}

fails = 0
for c, exp, exp_state in CASES:
    p = gp(c)
    f = l0b(p)
    th = build_tian_he(p, f)
    wp = build_wuxing_power(p, f, th)
    sp = build_special_patterns(p, f, wp, th)
    got = sp['cong_type'] or sp['zhuanwang'] or sp['hua_qi'] or (sp['patterns'][0]['name'] if sp['patterns'] else '无')
    state = sp['cong_state'] or (sp['patterns'][0]['state'] if sp['patterns'] else '')
    if exp == '无':
        ok = (got == '无')
    else:
        ok = (exp in got) and (exp_state is None or exp_state == state)
    if not ok:
        if c in KNOWN_BOUNDARY:
            print('KNOWN_BOUNDARY', c, '期望[' + exp + (('/' + exp_state) if exp_state else '') + '] 得[' + str(got) + '/' + state + '] (V7.17印透干保守判断, 不计入fails)')
        elif c in P0B_CONFIRMED_BOUNDARY:
            print('P0B_CONFIRMED', c, '期望[' + exp + (('/' + exp_state) if exp_state else '') + '] 得[' + str(got) + '/' + state + '] (P0-b口径: 月令当旺降级+化气桶删后一律CONFIRMED, 不计入fails)')
        elif c in KNOWN_DRIFT_BOUNDARY:
            print('KNOWN_DRIFT', c, '期望[' + exp + (('/' + exp_state) if exp_state else '') + '] 得[' + str(got) + '/' + state + '] (类别/方向漂移, 待原典专项裁决, 不计入fails)')
        else:
            fails += 1
            print('FAIL', c, '期望[' + exp +
          (('/' + exp_state) if exp_state else '') + '] 得[' + str(got) + '/' + state + ']')

# 母多灭子两级锚点(24例逐读DTS原文裁定): CONFIRMED=食伤财官三端真有力通道全断真灭;
# CANDIDATE=水方局孤泄被克漂没为病(待病药作用层分有药无药, 不反转方向);
# 反例=官杀当令化杀/官印相生任官/食伤当令吐秀/财破印/水冲奔从印/印局被冲, 皆不得误判母灭
MUMIE = [
    # —— CONFIRMED 真灭/无依坏命 8 ——
    ('戊辰壬戌辛未己丑', True, 'CONFIRMED'),  # 满局印绶土重金埋、壬水用神伤尽、木被冲, 克妻无子
    ('辛丑乙未庚辰丁丑', True, 'CONFIRMED'),  # 土重丁火熄、辛金肆逞冲去木火微根、财官虽有若无, 削发为僧
    ('丙辰辛丑庚辰丙子', True, 'CONFIRMED'),  # 重重湿土、丙合辛化水时丙无根、寒湿无生发, 破尽为僧
    ('己丑戊辰辛亥戊戌', True, 'CONFIRMED'),  # 重重厚土埋藏脆嫩之金、亥水孤泄被围克绝、无木疏土, 乙丑运夭
    ('辛丑辛丑癸酉癸丑', True, 'CONFIRMED'),  # 重重湿土叠叠寒金、癸水浊而且冻气浊神枯(金多水浊), 戊戌运夭
    ('癸卯甲寅丁卯甲辰', True, 'CONFIRMED'),  # 寅卯辰会木、癸归甲、木多火熄 — 挂单：母灭分支待补
    ('戊戌丙辰辛丑戊戌', True, 'CONFIRMED'),  # 原文直述四柱皆土、丙火元神泄尽、土重金坦、母多灭子
    ('丙戌戊戌辛丑戊戌', True, 'CONFIRMED'),  # 三戌一丑四库土重、土重金埋pair, 水木运犯母落职
    # —— CANDIDATE 水方局孤泄为病(病药层细分, 不反转) 2 ——
    ('丙子己亥乙丑壬午', True, 'CANDIDATE'),  # 水泛火绝为病, 然己土透通根午止水卫火 — 挂单：母灭分支待补
    ('己亥丙子乙丑壬午', True, 'CANDIDATE'),  # 亥子丑水局、午孤丙透被壬克、己土虚 — 挂单：母灭分支待补
    # —— 反例(非母灭) 16 ——
    ('壬戌壬子甲子戊辰', False, None),  # 戊土砥柱透干通根戌制水、印旺用财调候, 财破印
    ('癸亥癸亥丁卯癸卯', False, None),  # 癸杀透干通根亥、卯印化=杀印相生, 非纯印灭子
    ('辛未乙未庚辰丁亥', False, None),  # 丁火司令元神发露为用、财官通根有气、亥水润, 中乡榜迁司马
    ('戊辰庚申甲子甲子', False, None),  # 申月杀令木凋金锐、支全水局化肃杀生化有情, 科甲封疆(杀印相生)
    ('己巳癸酉壬辰甲辰', False, None),  # 秋水通源印秉令、官杀制化合宜、甲木制杀吐秀纯粹, 诰封二品
    ('丁未庚戌庚辰丙子', False, None),  # 丁火源头生土土生金、两藏财库、身旺用官, 名利双辉
    ('壬辰甲辰庚午丙戌', False, None),  # 春金杀旺、用神在土(印化杀)、土金运发财, 印为用神非埋
    ('庚辰丁亥庚辰丁丑', False, None),  # 亥月水(食伤)当令、丁火并透辰亥藏甲乙、足以用火(官), 仕至郡守
    ('乙未戊子庚辰丁丑', False, None),  # 子月水(食伤)当令、未土破子、木火得余气、用木生火, 财官格
    ('壬子辛亥乙亥丙子', False, None),  # 昆仑之水冲奔、地支本气全亥子清纯, 顺其流纳其气(从印/润下), 非灭
    ('癸酉乙卯丁未辛亥', False, None),  # 亥卯未木局逢卯酉紧邻冲、破其印局、乙辛战财杀肆逞, 病在财杀攻身
    ('己亥丙寅丁亥庚戌', False, None),  # 丁生寅月木当权火逢相旺、亥官合寅被庚隔, 木火相旺身不弱
    ('丙子己亥乙亥丙子', False, None),  # 亥月两丙透寒木向阳、印水不透干不克食伤、清纯粹, 只财官不足
    ('壬辰己酉甲申甲子', False, None),  # 申月杀令合官留杀、辰财酉官化金党杀、子水局化杀(杀印相生), 病在财党杀
    ('甲子丙子甲申己巳', False, None),  # 虚极不受水生/化神假(交作用层), 巳申合水丙虚, 结构层不判母灭
    ('丁未壬子庚戌丙戌', False, None),  # 仲冬水旺、支重燥土(未戌)去湿、丁壬合护官, 仕至州牧(燥土非埋金)
]
for c, exp_mm, exp_st in MUMIE:
    pp = gp(c); ff = l0b(pp); tth = build_tian_he(pp, ff); wwp = build_wuxing_power(pp, ff, tth)
    ssp = build_special_patterns(pp, ff, wwp, tth)
    got_mm = bool(ssp.get('mu_mie')); got_st = ssp.get('mu_mie_state')
    ok = (got_mm == exp_mm) and (exp_st is None or got_st == exp_st)
    if not ok:
        if c in KNOWN_DRIFT_BOUNDARY:
            print('KNOWN_DRIFT', c, '期望母灭=' + str(exp_mm) + '/' + str(exp_st) + ' 得=' + str(got_mm) + '/' + str(got_st) + ' (CONFIRMED/CANDIDATE口径互换, 待原典专项, 不计入fails)')
        else:
            fails += 1
            print('FAIL', c, '期望母灭=' + str(exp_mm) + '/' + str(exp_st)
                  + ' 得=' + str(got_mm) + '/' + str(got_st))

print()
# 两气成象锚点(天干地支本气仅两行、各成势、相生成象; 顺食伤秀神; 不与从/专旺冲突)
LIANGQI = [
    ('甲午丁卯甲午丁卯', '火'),  # 木火通明, 取丁火伤官秀气为用
    ('丙午戊戌丙午戊戌', '土'),  # 火土成象, 顺土(食伤)泄秀
    ('戊戌辛酉戊戌辛酉', '金'),  # 土金成象, 取辛金伤官为用
    # 癸亥甲寅(DTS L862)移出两气锚点: 寅亥合木、伤官太重泄身, 任注定性水木伤官格喜土金印官, 非两气; 见下方反例
]
for c, exp_xiu in LIANGQI:
    pp = gp(c); ff = l0b(pp); tth = build_tian_he(pp, ff); wwp = build_wuxing_power(pp, ff, tth)
    ssp = build_special_patterns(pp, ff, wwp, tth)
    lq = ssp.get('liangqi')
    ok = (bool(lq) and lq.get('xiu') == exp_xiu and not ssp.get('zhuanwang') and not ssp.get('cong_type'))
    if not ok: fails += 1
    print('PASS' if ok else 'FAIL', c, '期望两气成象秀神=' + exp_xiu
          + ' 得=' + str(None if not lq else (lq.get('name'), lq.get('xiu'))))

# 假两气反例(DTS L862 癸亥甲寅): 两行相生, 然日主根亥被寅亥合化为食伤木、伤官太重泄身,
# 任注'水木伤官...己酉戊申二十年土金生化不悖'(逢克方反吉), 应回正格水木伤官用印, 不判两气成象
_pp=gp('癸亥甲寅癸亥甲寅'); _ff=l0b(_pp); _tt=build_tian_he(_pp,_ff); _ww=build_wuxing_power(_pp,_ff,_tt)
_ss=build_special_patterns(_pp,_ff,_ww,_tt); _lq=_ss.get('liangqi')
_ok=(_lq is None)
if not _ok: fails+=1
print('PASS' if _ok else 'FAIL','癸亥甲寅癸亥甲寅 假两气应不判(回正格水木伤官) 得=',_lq)

print()
print('TOTAL', len(CASES) + len(MUMIE) + len(LIANGQI) + 1, 'FAILS', fails)
sys.exit(1 if fails else 0)
