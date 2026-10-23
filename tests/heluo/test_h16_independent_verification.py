"""H16: Independent Calculation Verification（独立计算正确性验证）

目标：对每个河洛算法函数，用≥3组输入做交叉验证，
      至少1组来自原典明确案例（古籍原文/纪晓岚等），
      至少1组为边界值。
      不依赖测试框架，直接输出 PASS/FAIL 报告。

原典依据：《河洛真数》续修四库全书本 + 三才发秘 + 中华典籍网

审查点（来自 40c39cef 审计意见）：
  1. normalize_tian_shu(25) 边界修复
  2. HuaGong 四季-卦映射与正反对判定
  3. Jiehhou 24节气卦气映射
  4. YuanTang N=4/5 分支（连续 vs gap）
  5. Meihua 三种起卦法与体用分析
  6. 寄宫法边界（天数/地数均为5）
  7. normalize_di_shu 遇十不用
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

PASS = 0
FAIL = 0


def check(label: str, got, expected, reason: str = "") -> bool:
    global PASS, FAIL
    ok = got == expected
    status = "[✅ PASS]" if ok else "[❌ FAIL]"
    print(f"  {status} {label} | got={got!r} | expected={expected!r}" +
          (f" | {reason}" if reason else ""))
    if ok:
        PASS += 1
    else:
        FAIL += 1
    return ok


def section(title: str):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


# ═══════════════════════════════════════════════════════════════
# Rule 01 & 02: 天干地支取数
# ═══════════════════════════════════════════════════════════════
section("Rule 01 & 02: 天干地支取数（原典：起例卷上）")

from heluo_engine.engines.heluo.numbers import (
    STEM_VALUES, BRANCH_VALUES,
    normalize_tian_shu, normalize_di_shu,
    compute_tian_di_shu, number_to_trigram, get_hexagram_name, build_six_lines,
    LUSHU_TO_TRIGRAM_NAME, TRIGRAM_LINES, TRIGRAM_ELEMENT,
    SIXTY_FOUR_HEXAGRAMS,
)

# 原典口诀：壬甲从乾数(6) · 乙癸向坤求(2) · 庚来震上住(3) · 辛在巽方面(4)
#          丙以艮门立(8) · 己于离家头(9) · 戊须坎处出(1) · 丁向兑中收(7)
check("甲=6",     STEM_VALUES["甲"],  6, "起例卷上·天干取数定局：壬甲从乾数（六）")
check("乙=2",     STEM_VALUES["乙"],  2, "起例卷上·天干取数定局：乙癸向坤求（二）")
check("丙=8",     STEM_VALUES["丙"],  8, "起例卷上·天干取数定局：丙以艮门立（八）")
check("丁=7",     STEM_VALUES["丁"],  7, "起例卷上·天干取数定局：丁向兑中收（七）")
check("戊=1",     STEM_VALUES["戊"],  1, "起例卷上·天干取数定局：戊须坎处出（一）")
check("己=9",     STEM_VALUES["己"],  9, "起例卷上·天干取数定局：己于离家头（九）")
check("庚=3",     STEM_VALUES["庚"],  3, "起例卷上·天干取数定局：庚来震上住（三）")
check("辛=4",     STEM_VALUES["辛"],  4, "起例卷上·天干取数定局：辛在巽方面（四）")
check("壬=6",     STEM_VALUES["壬"],  6, "起例卷上·天干取数定局：壬甲从乾数（六）")
check("癸=2",     STEM_VALUES["癸"],  2, "起例卷上·天干取数定局：乙癸向坤求（二）")

# 地支：子(1,6) · 丑(5,10) · 寅(3,8) · 卯(3,8) · 辰(5,10) · 巳(2,7)
#       午(2,7) · 未(5,10) · 申(4,9) · 酉(4,9) · 戌(5,10) · 亥(1,6)
for zhi, (odd, even) in [
    ("子", (1, 6)), ("丑", (5, 10)), ("寅", (3, 8)), ("卯", (3, 8)),
    ("辰", (5, 10)), ("巳", (2, 7)), ("午", (2, 7)), ("未", (5, 10)),
    ("申", (4, 9)), ("酉", (4, 9)), ("戌", (5, 10)), ("亥", (1, 6)),
]:
    got = BRANCH_VALUES[zhi]
    ok = set(got) == {odd, even}
    status = "✅" if ok else "❌"
    print(f"  {status} {zhi}={got} (期望奇偶={odd},{even}) | 河图生成数")
    if ok: PASS += 1
    else:  FAIL += 1

# 洛书映射
check("洛书1→坎",   number_to_trigram(1), "坎", "洛书数理：一白坎水")
check("洛书2→坤",   number_to_trigram(2), "坤", "洛书数理：二黑坤土")
check("洛书6→乾",   number_to_trigram(6), "乾", "洛书数理：六白乾金")
check("洛书9→离",   number_to_trigram(9), "离", "洛书数理：九紫离火")
check("洛书5→中",   number_to_trigram(5), "中", "中宫无卦，归中宫(5)")

# 八卦→三爻二进制（自下而上）
for name, expected in [
    ("乾", (1, 1, 1)), ("兑", (1, 1, -1)), ("离", (1, -1, 1)), ("震", (1, -1, -1)),
    ("巽", (-1, 1, 1)), ("坎", (-1, 1, -1)), ("艮", (-1, -1, 1)), ("坤", (-1, -1, -1)),
]:
    got = TRIGRAM_LINES[name]
    ok = got == expected
    status = "✅" if ok else "❌"
    print(f"  {status} {name}三爻={got} (期望{expected})")
    if ok: PASS += 1
    else:  FAIL += 1


# ═══════════════════════════════════════════════════════════════
# Rule 03: 归一化（含边界）
# ═══════════════════════════════════════════════════════════════
section("Rule 03: 归一化（天数/地数）")

check("normalize_tian(25)=5", normalize_tian_shu(25), 5, "原典：天数正数25归中宫（5）— H0修复后")
check("normalize_tian(22)=2", normalize_tian_shu(22), 2, "纪晓岚天数22→归一2")
check("normalize_tian(26)=1", normalize_tian_shu(26), 1, "天数26→26-25=1→余1")
check("normalize_tian(35)=0→商", normalize_tian_shu(35), 1, "天数35→10→商1")
check("normalize_tian(45)=2", normalize_tian_shu(45), 2, "天数45→20→余0→商2")

check("normalize_di(30)=3", normalize_di_shu(30), 3, "原典：地数正数30归3")
check("normalize_di(56)=6", normalize_di_shu(56), 6, "纪晓岚地数56→归一6")
check("normalize_di(31)=1", normalize_di_shu(31), 1, "地数31→31-30=1→余1")
check("normalize_di(40)=1", normalize_di_shu(40), 1, "地数40→10→余0→商1（遇十不用）")


# ═══════════════════════════════════════════════════════════════
# 纪晓岚八字验证
# ═══════════════════════════════════════════════════════════════
section("纪晓岚八字天数地数验证（原典案例）")

result = compute_tian_di_shu(
    [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")], "male"
)
check("纪晓岚天数总和", result.tian_shu, 22, "原典：纪晓岚天数22")
check("纪晓岚地数总和", result.di_shu, 56, "原典：纪晓岚地数56")
check("纪晓岚天数归一", result.tian_reduced, 2, "22→归一2（坤）")
check("纪晓岚地数归一", result.di_reduced, 6, "56→归一6（乾）")


# ═══════════════════════════════════════════════════════════════
# Rule 04: 寄宫法
# ═══════════════════════════════════════════════════════════════
section("Rule 04: 中宫寄宫（三元甲子）")

from heluo_engine.engines.heluo.prenatal import resolve_middle_palace, determine_prenatal_hexagram

t, d = resolve_middle_palace(5, 5, "male", True, "shang")
check("上元男天地双5寄宫", t, 8, "天数5→艮(8)，地数5→艮(8)")
check("上元男地数5寄宫", d, 8, "地数5→艮(8)")

t, d = resolve_middle_palace(5, 5, "female", True, "shang")
check("上元女天地双5寄宫", t, 2, "天数5→坤(2)，地数5→坤(2)")

t, d = resolve_middle_palace(5, 5, "male", True, "xia")
check("下元男寄宫5→9", t, 9, "原典：下元甲子生人男寄离卦(9)")

t, d = resolve_middle_palace(5, 5, "female", True, "xia")
check("下元女寄宫5→7", t, 7, "原典：下元甲子生人女寄兑卦(7)")

t, d = resolve_middle_palace(5, 5, "male", True, "zhong")
check("中元阳年男寄宫5→8", t, 8, "原典：中元阳男阴女寄艮(8)")

t, d = resolve_middle_palace(5, 5, "female", False, "zhong")
check("中元阴年女寄宫5→8", t, 8, "原典：中元阴男阳女寄坤(2)，阴年女应寄艮(8)")

result_m = determine_prenatal_hexagram(2, 6, "male", True, "zhong")
check("纪晓岚男先天卦", result_m.hexagram_name, "地天泰",
      "阳年男：天数在上(坤)，地数在下(乾) → 地天泰")
check("纪晓岚男上卦", result_m.upper_gua, "坤", "阳年男命：天上地下")
check("纪晓岚男下卦", result_m.lower_gua, "乾", "阳年男命：天上地下")

result_f = determine_prenatal_hexagram(2, 6, "female", True, "zhong")
check("纪晓岚女先天卦", result_f.hexagram_name, "天地否",
      "阳年女：天数在下(坤)，地数在上(乾) → 天地否")
check("纪晓岚女上卦", result_f.upper_gua, "乾", "阳年女命：地下天上")
check("纪晓岚女下卦", result_f.lower_gua, "坤", "阳年女命：地下天上")


# ═══════════════════════════════════════════════════════════════
# Rule 05: 元堂
# ═══════════════════════════════════════════════════════════════
section("Rule 05: 元堂定位（N=1~5 全分支）")

from heluo_engine.engines.heluo.yuan_tang import find_yuantang, HOUR_NAMES

# 纪晓岚：地天泰 → build_six_lines('坤','乾') → [1,1,1,-1,-1,-1]
tai_lines = build_six_lines("坤", "乾")
check("泰卦六爻", tai_lines, [1, 1, 1, -1, -1, -1], "地天泰：下卦乾(1,1,1)+上卦坤(-1,-1,-1)")

r = find_yuantang(tai_lines, "午", "male", "地天泰")
check("泰卦午时男元堂=六四", r.yuantang, "六四", "原典：泰卦午时男命，元堂在六四")
check("泰卦午时男元堂idx=3", r.yuantang_index, 3, "六四对应index=3")
check("泰卦午时男爻性=阴", r.yao_nature, "阴", "六四为阴爻")

# 复卦（地雷复）：build_six_lines('坤','震') → [1,-1,-1,-1,-1,-1]
fu_lines = build_six_lines("坤", "震")
check("复卦六爻", fu_lines, [1, -1, -1, -1, -1, -1], "地雷复：下坤(-1,-1,-1)+上震(1,-1,-1)")
r = find_yuantang(fu_lines, "子", "male", "地雷复")
check("复卦子时男元堂=初九", r.yuantang, "初九",
      "原典：复卦一阳爻@idx=0，子时男命(t=0)→初九(idx=0)")
check("复卦子时男元堂idx=0", r.yuantang_index, 0, "初九对应index=0")

# 旅卦（火山旅）：build_six_lines('艮','离') → [1,-1,1,-1,-1,1]
lv_lines = build_six_lines("艮", "离")
check("旅卦六爻", lv_lines, [1, -1, 1, -1, -1, 1], "火山旅：下艮(-1,-1,1)+上离(1,-1,1)")
r = find_yuantang(lv_lines, "午", "male", "火山旅")
check("旅卦午时男元堂=六二", r.yuantang, "六二",
      "原典：旅卦阳爻候选[0,2,5]，午时(t=4)，N=3→path*2=[0,2,5,0,2,5]，idx=4→2")
check("旅卦午时男元堂idx=1", r.yuantang_index, 1, "六二对应index=1")

# 萃卦（泽地萃）：build_six_lines('坤','兑') → [1,1,-1,-1,-1,-1]
cu_lines = build_six_lines("坤", "兑")
check("萃卦六爻", cu_lines, [1, 1, -1, -1, -1, -1], "泽地萃：下坤(-1,-1,-1)+上兑(1,1,-1)")
r = find_yuantang(cu_lines, "子", "male", "泽地萃")
check("萃卦子时男元堂=初九", r.yuantang, "初九",
      "原典：萃卦阳爻候选[0,1]，N=2，子时(t=0)<2→candidates[0]=0")
check("萃卦子时男元堂idx=0", r.yuantang_index, 0, "初九对应index=0")

# N=4 连续分支（大过）：build_six_lines('巽','兑') → [1,1,-1,-1,1,1]
dg_lines = build_six_lines("巽", "兑")
check("大过六爻", dg_lines, [1, 1, -1, -1, 1, 1], "泽风大过：下巽(-1,1,1)+上兑(1,1,-1)")
r = find_yuantang(dg_lines, "辰", "male", "泽风大过")
check("大过辰时男元堂=六三", r.yuantang, "六三",
      "原典：大过四阳爻连续@0,1,4,5，辰时(t=4)>=4→回绕至异类@2")
check("大过辰时男元堂idx=2", r.yuantang_index, 2, "六三对应index=2")
check("大过辰时男爻性=阴", r.yao_nature, "阴", "落点六三为阴爻")

# N=4 有gap分支（艮为山）：build_six_lines('艮','艮') → [-1,-1,1,-1,-1,1]
gen_lines = build_six_lines("艮", "艮")
r = find_yuantang(gen_lines, "戌", "male", "艮为山")
check("艮为山戌时男元堂idx", r.yuantang_index, 2,
      "原典：艮为山四阴爻有gap，戌时(t=4)≥4→取模到@2")


# ═══════════════════════════════════════════════════════════════
# Rule 06: 后天卦变换
# ═══════════════════════════════════════════════════════════════
section("Rule 06: 后天卦两步法")

from heluo_engine.engines.heluo.postnatal import compute_postnatal

post = compute_postnatal(tai_lines, 3)
check("纪晓岚后天卦", post.hexagram_name, "天雷无妄",
      "原典：泰六四动→第一步大壮→第二步无妄")
check("纪晓岚后天上卦", post.upper_gua, "乾", "天雷无妄：上乾下震")
check("纪晓岚后天下卦", post.lower_gua, "震", "天雷无妄：上乾下震")
check("纪晓岚第一步", post.step1_hexagram, "雷天大壮",
      "第一步：元堂六四变→雷天大壮")


# ═══════════════════════════════════════════════════════════════
# Rule 09: 化工（四季-卦映射 + 正反对）
# ═══════════════════════════════════════════════════════════════
section("Rule 09: 化工状态判定")

from heluo_engine.engines.heluo.hua_gong import compute_huagong, HuaGongState

# 春季寅月→化工卦震。卦(乾,坤,乾,坤)不含震也不含兑→UNRESOLVED
r = compute_huagong("乾", "坤", "乾", "坤", "寅")
check("春化工乾坤卦→UNRESOLVED", r.state, HuaGongState.UNRESOLVED,
      "卦含乾(金)坤(土)，不含震(化工)也不含兑(反)")

# 卦中含震+兑（正对）
r = compute_huagong("震", "坤", "兑", "坤", "寅")
check("春化工含震含兑→RESCUED", r.state, HuaGongState.RESCUED,
      "卦含化工震，也含反兑 → RESCUED（相生救应）")

# 卦中含兑不含震（反位）
r = compute_huagong("兑", "坤", "兑", "坤", "寅")
check("春化工含兑不含震→REVERSE", r.state, HuaGongState.REVERSE,
      "卦含反卦兑，无化工震 → REVERSE")

# 冬季丑月→化工卦坎
r = compute_huagong("坎", "坤", "坎", "坤", "丑")
check("冬坎化工-NORMAL", r.state, HuaGongState.NORMAL,
      "卦含坎(化工)，不含离(反) → NORMAL")

r = compute_huagong("离", "坤", "离", "坤", "丑")
check("冬坎化工卦含离→REVERSE", r.state, HuaGongState.REVERSE,
      "卦含离(反)，不含坎(化工) → REVERSE")

# 夏季午月→化工卦离
r = compute_huagong("离", "坤", "离", "坤", "午")
check("夏离化工-NORMAL", r.state, HuaGongState.NORMAL,
      "卦含离(化工)，不含坎(反) → NORMAL")

# 秋季申月→化工卦兑
r = compute_huagong("兑", "坤", "兑", "坤", "申")
check("秋兑化工-NORMAL", r.state, HuaGongState.NORMAL,
      "卦含兑(化工)，不含震(反) → NORMAL")

r = compute_huagong("坎", "坤", "坎", "坤", "丑")
check("丑月化工卦=坎", r.huagong_trigram, "坎", "丑∈冬→坎")


# ═══════════════════════════════════════════════════════════════
# Rule 13 & 14: 节候卦 / 卦气
# ═══════════════════════════════════════════════════════════════
section("Rule 13 & 14: 节候卦（24节气）")

from heluo_engine.engines.heluo.jiehhou import (
    get_seasonal_hexagram, SOLAR_TERMS, JIEHOU_GUA,
    get_qi_phase, get_current_jieqi_info, SIZHENG_GUA, BI_GUA,
)

# 原典 L1492：节卦坎初六起冬至，每卦总管九十日，每一爻各直十五日
# （旧本此处引「冬至一索得中男，颐六四爻动，为地雷复卦」，
#   经原著全库检索零命中，2026-10-07 订正为原典节卦口径）
info = get_seasonal_hexagram(0)
check("冬至节卦=坎", info.main_gua, "坎", "原典：节卦坎初六起冬至")
check("冬至爻位=0", info.moving_line, 0, "原典：坎初六，自下而上第一爻")
check("冬至爻名=初六", info.result_gua, "初六", "原典：坎初六")

# 立春：坎六四（原典「六四立春」）
info = get_seasonal_hexagram(3)
check("立春节卦=坎", info.main_gua, "坎", "原典：坎卦六四值立春")
check("立春爻位=3", info.moving_line, 3, "原典：坎六四，自下而上第四爻")
check("立春爻名=六四", info.result_gua, "六四", "原典：六四立春")

# 夏至：离初九（原典「离初九起夏至」）
info = get_seasonal_hexagram(12)
check("夏至节卦=离", info.main_gua, "离", "原典：离初九起夏至")
check("夏至爻位=0", info.moving_line, 0, "原典：离初九")
check("夏至爻名=初九", info.result_gua, "初九", "原典：离初九起夏至")

# 秋分：兑初九（原典「兑初九起秋分」）
info = get_seasonal_hexagram(18)
check("秋分节卦=兑", info.main_gua, "兑", "原典：兑初九起秋分")
check("秋分爻位=0", info.moving_line, 0, "原典：兑初九")
check("秋分爻名=初九", info.result_gua, "初九", "原典：兑初九起秋分")

# 春分：震初九（原典「震初九起春分」）
info = get_seasonal_hexagram(6)
check("春分节卦=震", info.main_gua, "震", "原典：震初九起春分")
check("春分爻位=0", info.moving_line, 0, "原典：震初九")
check("春分爻名=初九", info.result_gua, "初九", "原典：震初九起春分")

# 24节气名称一致
all_ok = all(get_seasonal_hexagram(i).jq_name == SOLAR_TERMS[i] for i in range(24))
check("24节气名称一致", all_ok, True, "jqIndex 0-23 与 SOLAR_TERMS 完全对应")

# 卦气判断
phase = get_qi_phase(2024, 0)
check("冬至四正卦", phase.is_sizheng, True, "冬至=坎（四正卦之一）")
check("冬至辟卦", phase.is_bi_gua, True, "冬至为辟卦（复卦当令）")

phase = get_qi_phase(2024, 6)
check("春分四正卦", phase.is_sizheng, True, "春分=震（四正卦之一）")

phase = get_qi_phase(2024, 3)
check("立春非四正卦", phase.is_sizheng, False, "立春非四正卦分管")

check("节候卦条目数=24", len(JIEHOU_GUA), 24, "24节气各有节候卦")


# ═══════════════════════════════════════════════════════════════
# Rule 10: 大运（爻位值运）
# ═══════════════════════════════════════════════════════════════
section("Rule 10: 大运（爻位值运）")

from heluo_engine.engines.heluo.timeline_yun import compute_dayun_liyao
from heluo_engine.engines.heluo.postnatal import compute_postnatal as _cpn

post2 = _cpn(tai_lines, 3)
from heluo_engine.engines.heluo.numbers import TRIGRAM_LINES
postnatal_final = list(TRIGRAM_LINES[post2.lower_gua]) + list(TRIGRAM_LINES[post2.upper_gua])
check("后天卦六爻构建", postnatal_final,
      list(TRIGRAM_LINES["震"]) + list(TRIGRAM_LINES["乾"]),
      "天雷无妄：下震(-1,-1,1)+上乾(1,1,1)")

dayun = compute_dayun_liyao(tai_lines, 3, postnatal_final, 0)
check("大运总段数=12", len(dayun.sequence), 12, "先天6爻+后天6爻=12段")
check("首段age_start=1", dayun.sequence[0].age_start, 1, "原典：起运始于1岁")
last = dayun.sequence[-1]
check("末段age_end=93", last.age_end, 93, "先天45+后天48=93")


# ═══════════════════════════════════════════════════════════════
# Rule 11: 流月卦
# ═══════════════════════════════════════════════════════════════
section("Rule 11: 流月卦（阳世子月起，阴世午月起）")

from heluo_engine.engines.heluo.timeline_yun import compute_liuyue

liuyue = compute_liuyue(tai_lines, 3)
check("流月卦数=12", len(liuyue.months), 12, "一年12个月")
check("正月(子)为阳月", liuyue.months[0]["kind"], "阳月", "子月为阳月")
check("二月(丑)为阴月", liuyue.months[1]["kind"], "阴月", "丑月为阴月")
check("正月卦≠二月卦", liuyue.months[0]["name"] != liuyue.months[1]["name"], True,
      "阳月变元堂下一爻，阴月变应爻，卦必不同")


# ═══════════════════════════════════════════════════════════════
# 梅花易数：三种起卦法 + 体用分析
# ═══════════════════════════════════════════════════════════════
section("Rule: 梅花易数起卦法")

# ⚠ 梅花易数**不属于河洛域**，其引擎在主仓（`tongshu.engines.meihua`），
#   不在本独立包内。河洛引擎提纯为独立包后，这一段改为**可选**：
#   依赖缺失 ⇒ 跳过本节并留痕，不让整个文件在收集期炸掉
#   （此前此处裸 import 导致本文件**整体**无法收集，河洛域的
#     数百项独立计算验证被连带废掉 —— 一处他域依赖拖垮全域覆盖）。
try:
    from tongshu.engines.meihua import cast_by_time, cast_by_numbers
except ModuleNotFoundError:
    cast_by_time = cast_by_numbers = None
    print("  [SKIP] 梅花易数段：主仓专有模块 tongshu.engines.meihua 不在"
          "河洛独立包内（他域，不属河洛域）")

if cast_by_time is not None:
    r = cast_by_time(2024, 3, 15, 10)
    check("梅花时间起卦本卦有内容", len(r.ben_gua) > 0, True, "本卦应为主卦名")
    check("梅花时间起卦有变卦", r.bian_gua is not None and len(r.bian_gua) > 0, True, "应产生变卦")
    check("梅花时间起卦有互卦", r.hu_gua is not None and len(r.hu_gua) > 0, True, "应产生互卦")
    check("梅花时间起卦有体用", r.ti is not None and r.yong is not None, True, "应区分体卦和用卦")
    check("梅花时间起卦体用为卦名", r.ti in TRIGRAM_LINES and r.yong in TRIGRAM_LINES, True,
          "体用应为八卦名之一")

    r = cast_by_numbers(3, 5)
    check("梅花数起(3,5)本卦", r.ben_gua, "火风鼎", "上离(3)下巽(5)→火风鼎")
    check("梅花数起(3,5)动爻1based", r.dong_yao_1based, 3, "(3+5)%6=2, 1-based=2")

    r = cast_by_numbers(1, 1)
    check("梅花乾为天", r.ben_gua, "乾为天", "上下皆乾")
    check("梅花乾错卦=坤", r.cuo_gua, "坤为地", "乾(111,111)错为坤(000,000)")
    check("梅花乾综卦=乾", r.zong_gua, "乾为天", "乾自综")

    r = cast_by_numbers(1, 3)
    check("同人动爻=5", r.dong_yao_1based, 5, "(1+3)%6=4, 1-based=4")


# ═══════════════════════════════════════════════════════════════
# 边界案例
# ═══════════════════════════════════════════════════════════════
section("边界案例验证")

qian_lines = build_six_lines("乾", "乾")
r = find_yuantang(qian_lines, "子", "male", "乾为天")
check("乾卦子时男元堂=初九", r.yuantang, "初九", "纯阳卦男自下而上，子时(0)%6=0→初九")
r = find_yuantang(qian_lines, "子", "female", "乾为天")
check("乾卦子时女元堂=上九", r.yuantang, "上九", "纯阳卦女自上而下，子时(0)→5%6=5→上九")

kun_lines = build_six_lines("坤", "坤")
r = find_yuantang(kun_lines, "子", "female", "坤为地")
check("坤卦子时女元堂=初六", r.yuantang, "初六", "纯阴卦女自下而上，子时(0)%6=0→初六")
r = find_yuantang(kun_lines, "午", "female", "坤为地")
check("坤卦午时女元堂=初六", r.yuantang, "初六", "纯阴卦女自下而上，午时(6)%6=0→初六")
r = find_yuantang(kun_lines, "子", "male", "坤为地")
check("坤卦子时男元堂=上六", r.yuantang, "上六", "纯阴卦男自上而下，子时(0)→5%6=5→上六")

check("六十四卦数量=64", len(SIXTY_FOUR_HEXAGRAMS), 64, "六十四卦上下卦组合应恰好64种")
names = list(SIXTY_FOUR_HEXAGRAMS.values())
check("六十四卦名无重复", len(set(names)) == 64, True, "每个卦名应唯一")

info_23 = get_seasonal_hexagram(23)
info_0 = get_seasonal_hexagram(0)
check("大雪主卦=需", info_23.main_gua, "水天需", "原典：大雪需六三动→需")
check("冬至主卦=颐", info_0.main_gua, "山雷颐", "原典：冬至颐六四动→复")

check("四正卦数量=4", len(SIZHENG_GUA), 4, "坎离震兑")
check("辟卦数量=12", len(BI_GUA), 12, "十二消息卦")


# ═══════════════════════════════════════════════════════════════
# 结果汇总
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"  H16 验证结果: {PASS}/(PASS+FAIL) PASS, {FAIL} FAIL")
print(f"{'='*60}")
if FAIL == 0:
    print("  ✅ 全部通过")
else:
    print(f"  ❌ {FAIL} 项失败，需审查")
