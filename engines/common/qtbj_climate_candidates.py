# -*- coding: utf-8 -*-
"""P160 QTBJ 调候候选查表视图 · 第二刀（旁路只读查表, 不碰旧 climate 主链）

只做一件事:
  日干 × 月令 -> 《穷通宝鉴》原文所载调候干及其先后次序(纯查表候选, 并列不裁)。

与第一刀 PZZQ 格神视图并列、独立 namespace, 不混成"总用神":
  - 格局用神(PZZQ) 与 调候用神(QTBJ) 各自记录, 互不覆盖;
  - 不判断调候干是否透出/得用, 不判富贵/岁运喜忌/从化/降级;
  - order 只是原文所载先后次序, 非评分/权重/优先级裁决;
  - 未在本表录入的日干月令一律 NOT_REGISTERED, 不编造、不补全。

【2026-10-01 三源合并重裁定 · 单一真相源 _qtbj_FINAL_120.json】
  原表(HEAD b6d298e9) 与 15:09 改写版 存在 51 处相左, 经双底本逐格取证后重建。
  底本 A = registries/source/raw/QTBJ_穷通宝鉴_原文A版_最终原著版.txt (md5 551db46d)
  底本 B = registries/source/raw/QTBJ_穷通宝鉴_原文.md         (md5 e6e3204e)
  裁决单 = REPORT_QTBJ_120_三源合并取证单.md
  覆盖: 双源单月 69 / B单月 32 / 合并章拆分 19 = 120, 零 GAP。
  条件句(酌用/亦可/参酌/权宜/无X用Y)不入定序, 已剔除。
"""
from typing import Any, Dict, List, Optional

# 日干 × 月令 -> 调候候选干(按原文先后次序)
# 120 格全表; 每格带原典锚点(QTBJ-xxx-xxx)
_CLIMATE_TABLE: Dict = {
    ('甲', '寅'): {  # 正月甲木: 得丙癸逢, 寒木向阳
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-003-002'],
    },
    ('甲', '卯'): {  # 二月甲木: 阳刃架煞专用庚, 要财资煞
        'candidates': [('庚', 1)],
        'evidence_refs': ['QTBJ-004-001'],
    },
    ('甲', '辰'): {  # 三月甲木: 先取庚金, 次用壬水
        'candidates': [('庚', 1), ('壬', 2)],
        'evidence_refs': ['QTBJ-005-001'],
    },
    ('甲', '巳'): {  # 四月甲木: 先癸後丁, 庚金太多甲反受病
        'candidates': [('癸', 1), ('丁', 2)],
        'evidence_refs': ['QTBJ-006-001'],
    },
    ('甲', '午'): {  # 五六月甲木: 五月先癸後丁, 庚金次之
        'candidates': [('癸', 1), ('丁', 2), ('庚', 3)],
        'evidence_refs': ['QTBJ-007-001'],
    },
    ('甲', '未'): {  # 六月甲木: 三伏生寒先丁後庚, 无癸亦可
        'candidates': [('丁', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-007-001'],
    },
    ('甲', '申'): {  # 七月甲木: 丁火为尊，庚金次之(甲为日主引助，不入用神序列)
        'candidates': [('丁', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-008-001'],
    },
    ('甲', '酉'): {  # 八月甲木: 丁火为先, 次用丙火, 庚金再次
        'candidates': [('丁', 1), ('丙', 2), ('庚', 3)],
        'evidence_refs': ['QTBJ-009-001'],
    },
    ('甲', '戌'): {  # 九月甲木: 独爱丁火, 壬癸滋扶, 庚金得所
        'candidates': [('丁', 1), ('壬', 2), ('癸', 3)],
        'evidence_refs': ['QTBJ-010-001'],
    },
    ('甲', '亥'): {  # 十月甲木: 庚丁为要, 丙火次之, 须戊土制水
        'candidates': [('庚', 1), ('丁', 2), ('丙', 3), ('戊', 4)],
        'evidence_refs': ['QTBJ-011-001'],
    },
    ('甲', '子'): {  # 十一月甲木: 丁先庚後, 丙火佐之
        'candidates': [('丁', 1), ('庚', 2), ('丙', 3)],
        'evidence_refs': ['QTBJ-012-001'],
    },
    ('甲', '丑'): {  # 十二月甲木: 先用庚劈甲, 方引丁火, 故丁次之
        'candidates': [('庚', 1), ('丁', 2)],
        'evidence_refs': ['QTBJ-013-001'],
    },
    ('乙', '寅'): {  # 正月乙木: 以丙火为先, 癸水次之
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-014-002'],
    },
    ('乙', '卯'): {  # 二月乙木: 以丙为君, 癸为臣
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-015-001'],
    },
    ('乙', '辰'): {  # 三月乙木: 先癸後丙
        'candidates': [('癸', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-016-001'],
    },
    ('乙', '巳'): {  # 四月乙木: 端取癸水为尊, 丙火酌用
        'candidates': [('癸', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-017-001'],
    },
    ('乙', '午'): {  # 五月乙木: 上半月专用癸, 下半月丙癸齐用
        'candidates': [('癸', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-018-001'],
    },
    ('乙', '未'): {  # 六月乙木: 柱多金水丙火为尊, 癸水透干大富
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-019-002'],
    },
    ('乙', '申'): {  # 七月乙木: 丙癸透干, 又加己出埋金
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-020-001'],
    },
    ('乙', '酉'): {  # 八月乙木: 白露後专用癸, 秋分後丙癸两透
        'candidates': [('癸', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-021-001'],
    },
    ('乙', '戌'): {  # 九月乙木: 必赖癸水滋养, 又遇辛金发水之源
        'candidates': [('癸', 1), ('辛', 2)],
        'evidence_refs': ['QTBJ-022-001'],
    },
    ('乙', '亥'): {  # 十月乙木: 取丙为用, 戊土次之
        'candidates': [('丙', 1), ('戊', 2)],
        'evidence_refs': ['QTBJ-023-001'],
    },
    ('乙', '子'): {  # 十一月乙木: 端用丙火, 不宜用癸
        'candidates': [('丙', 1)],
        'evidence_refs': ['QTBJ-024-001'],
    },
    ('乙', '丑'): {  # 十二月乙木: 寒谷回春专用丙
        'candidates': [('丙', 1)],
        'evidence_refs': ['QTBJ-025-001'],
    },
    ('丙', '寅'): {  # 正月丙火: 取壬为尊, 庚金佐之
        'candidates': [('壬', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-027-002'],
    },
    ('丙', '卯'): {  # 二月丙火: 端用壬水, 壬透天干不见丁化
        'candidates': [('壬', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-028-001'],
    },
    ('丙', '辰'): {  # 三月丙火: 用壬水, 成土局取甲木为辅, 忌庚出制甲
        'candidates': [('壬', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-029-001'],
    },
    ('丙', '巳'): {  # 四月丙火: 专用壬水, 庚金为水之源
        'candidates': [('壬', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-030-001'],
    },
    ('丙', '午'): {  # 五月丙火: 得壬高透方为上命
        'candidates': [('壬', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-031-001'],
    },
    ('丙', '未'): {  # 六月丙火: 壬水为用, 取庚辅佐
        'candidates': [('壬', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-032-001'],
    },
    ('丙', '申'): {  # 七月丙火: 太阳转西仍用壬水辅映, 三秋甲庚丙并用
        'candidates': [('壬', 1)],
        'evidence_refs': ['QTBJ-033-001'],
    },
    ('丙', '酉'): {  # 八月丙火: 仍用壬水辅映, 甲木为佐
        'candidates': [('壬', 1)],
        'evidence_refs': ['QTBJ-034-001'],
    },
    ('丙', '戌'): {  # 九月丙火: 必须先用甲木, 次取壬水
        'candidates': [('甲', 1), ('壬', 2)],
        'evidence_refs': ['QTBJ-035-001'],
    },
    ('丙', '亥'): {  # 十月丙火: 得见甲戊庚出干, 水旺宜戊
        'candidates': [('甲', 1), ('戊', 2), ('庚', 3)],
        'evidence_refs': ['QTBJ-036-001'],
    },
    ('丙', '子'): {  # 十一月丙火: 壬水为最, 戊土佐之, 壬甲两透
        'candidates': [('壬', 1), ('戊', 2)],
        'evidence_refs': ['QTBJ-037-001'],
    },
    ('丙', '丑'): {  # 十二月丙火: 喜壬为用, 甲藏则秀才
        'candidates': [('壬', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-038-001'],
    },
    ('丁', '寅'): {  # 正月丁火: 非庚不能劈甲, 先庚後壬
        'candidates': [('庚', 1), ('壬', 2)],
        'evidence_refs': ['QTBJ-039-001'],
    },
    ('丁', '卯'): {  # 二月丁火: 先庚後甲
        'candidates': [('庚', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-040-001'],
    },
    ('丁', '辰'): {  # 三月丁火: 先用甲木引丁制土, 次看庚金
        'candidates': [('甲', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-041-001'],
    },
    ('丁', '巳'): {  # 四月丁火: 取甲引丁必用庚劈甲, 甲多取庚为先
        'candidates': [('庚', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-042-001'],
    },
    ('丁', '午'): {  # 五月丁火: 建禄不宜乱用甲, 庚壬两透科甲
        'candidates': [('壬', 1)],
        'evidence_refs': ['QTBJ-043-002'],
    },
    ('丁', '未'): {  # 六月丁火: 专取甲木, 壬水次之
        'candidates': [('甲', 1), ('壬', 2)],
        'evidence_refs': ['QTBJ-044-001'],
    },
    ('丁', '申'): {  # 七月丁火: 端用甲木，仍取庚劈甲(丙为『或借』替代，非必用)
        'candidates': [('甲', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-045-001'],
    },
    ('丁', '酉'): {  # 八九月丁火: 甲庚丙并用
        'candidates': [('甲', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-045-001'],
    },
    ('丁', '戌'): {  # 八九月丁火: 甲庚丙并用
        'candidates': [('甲', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-045-001'],
    },
    ('丁', '亥'): {  # 十月丁火: 端用庚甲, 冬丁有甲不怕水多
        'candidates': [('庚', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-046-002'],
    },
    ('丁', '子'): {  # 十一月丁火: 三冬丁火端用庚甲
        'candidates': [('甲', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-046-002'],
    },
    ('丁', '丑'): {  # 十一十二月丁火: 端用庚甲
        'candidates': [('甲', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-046-002'],
    },
    ('戊', '寅'): {  # 正二月戊土: 即有甲癸无丙除寒富贵艰辛, 丙甲癸三者不可缺一
        'candidates': [('丙', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-048-001'],
    },
    ('戊', '卯'): {  # 正二月戊土: 无丙者富贵艰辛
        'candidates': [('丙', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-048-001'],
    },
    ('戊', '辰'): {  # 三月戊土: 不见丙甲癸者愚贱, 两癸透者生员
        'candidates': [('甲', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-048-001'],
    },
    ('戊', '巳'): {  # 四月戊土: 先用甲疏劈, 次取丙癸为佐
        'candidates': [('甲', 1), ('丙', 2), ('癸', 3)],
        'evidence_refs': ['QTBJ-048-004'],
    },
    ('戊', '午'): {  # 五月戊土: 先看壬水, 次取甲木, 丙火酌用
        'candidates': [('壬', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-049-001'],
    },
    ('戊', '未'): {  # 六月戊土: 先看癸水, 次用丙火甲木
        'candidates': [('癸', 1), ('丙', 2), ('甲', 3)],
        'evidence_refs': ['QTBJ-050-001'],
    },
    ('戊', '申'): {  # 七月戊土: 先丙後癸, 甲木次之
        'candidates': [('丙', 1), ('癸', 2), ('甲', 3)],
        'evidence_refs': ['QTBJ-051-001'],
    },
    ('戊', '酉'): {  # 八月戊土: 先丙後癸, 不必木疏
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-052-001'],
    },
    ('戊', '戌'): {  # 九月戊土: 不可专用丙, 先看甲木, 次取癸水
        'candidates': [('甲', 1), ('癸', 2), ('丙', 3)],
        'evidence_refs': ['QTBJ-053-001'],
    },
    ('戊', '亥'): {  # 十月戊土: 先用甲木, 次取丙火
        'candidates': [('甲', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-054-001'],
    },
    ('戊', '子'): {  # 十一十二月戊土: 端用丙火, 甲木佐之
        'candidates': [('丙', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-054-001'],
    },
    ('戊', '丑'): {  # 十一十二月戊土: 端用丙火, 甲木佐之
        'candidates': [('丙', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-054-001'],
    },
    ('己', '寅'): {  # 正月己土: 丙为尊, 得丙照暖万物自生
        'candidates': [('丙', 1)],
        'evidence_refs': ['QTBJ-055-001'],
    },
    ('己', '卯'): {  # 二月己土: 先取甲木疏之, 次取癸水润之, 一丙出透
        'candidates': [('甲', 1), ('癸', 2), ('丙', 3)],
        'evidence_refs': ['QTBJ-056-001'],
    },
    ('己', '辰'): {  # 三月己土: 先丙後癸, 土暖而润, 随用甲疏
        'candidates': [('丙', 1), ('癸', 2), ('甲', 3)],
        'evidence_refs': ['QTBJ-057-001'],
    },
    ('己', '巳'): {  # 四五六六月己土: 端用癸水, 丙火酌用
        'candidates': [('癸', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-058-001'],
    },
    ('己', '午'): {  # 四五六六月己土: 端用癸水, 丙火酌用
        'candidates': [('癸', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-058-001'],
    },
    ('己', '未'): {  # 四五六六月己土: 端用癸水, 丙火酌用
        'candidates': [('癸', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-058-001'],
    },
    ('己', '申'): {  # 七八九月己土: 须丙火温之, 癸水润之
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-059-001'],
    },
    ('己', '酉'): {  # 七八九月己土: 须丙火温之, 癸水润之
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-059-001'],
    },
    ('己', '戌'): {  # 七八九月己土: 须丙火温之, 癸水润之
        'candidates': [('丙', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-059-002'],
    },
    ('己', '亥'): {  # 十十一十二月己土: 调候以丙为上, 壬旺兼用戊
        'candidates': [('丙', 1)],
        'evidence_refs': ['QTBJ-060-001'],
    },
    ('己', '子'): {  # 十十一十二月己土: 调候以丙为上
        'candidates': [('丙', 1)],
        'evidence_refs': ['QTBJ-060-001'],
    },
    ('己', '丑'): {  # 十十一十二月己土: 调候以丙为上
        'candidates': [('丙', 1)],
        'evidence_refs': ['QTBJ-060-001'],
    },
    ('庚', '寅'): {  # 正月庚金: 先用丙暖庚性, 须甲疏泄
        'candidates': [('丙', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-062-001'],
    },
    ('庚', '卯'): {  # 二月庚金: 专用丁火, 借甲引丁
        'candidates': [('丁', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-063-002'],
    },
    ('庚', '辰'): {  # 三月庚金: 先甲後丁, 旺土须甲, 顽金宜丁
        'candidates': [('甲', 1), ('丁', 2)],
        'evidence_refs': ['QTBJ-064-001'],
    },
    ('庚', '巳'): {  # 四月庚金: 先壬水, 次取戊土, 丙火佐
        'candidates': [('壬', 1), ('戊', 2), ('丙', 3)],
        'evidence_refs': ['QTBJ-065-001'],
    },
    ('庚', '午'): {  # 五月庚金: 专用壬水, 癸又次之
        'candidates': [('壬', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-066-001'],
    },
    ('庚', '未'): {  # 六月庚金: 先用丁火, 次取甲木
        'candidates': [('丁', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-067-001'],
    },
    ('庚', '申'): {  # 七月庚金: 专用丁火煆炼, 次取木引丁
        'candidates': [('丁', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-068-001'],
    },
    ('庚', '酉'): {  # 八月庚金: 用丁甲, 丙不可少
        'candidates': [('丁', 1), ('甲', 2), ('丙', 3)],
        'evidence_refs': ['QTBJ-069-001'],
    },
    ('庚', '戌'): {  # 九月庚金: 宜先用甲疏, 後用壬洗; 丁火炼金候(土重埋金局, 局内有官火根时入候)
        'candidates': [('甲', 1), ('壬', 2), ('丁', 3)],
        'evidence_refs': ['QTBJ-070-001'],
    },
    ('庚', '亥'): {  # 十月庚金: 非丁莫造, 非丙不暖
        'candidates': [('丁', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-071-001'],
    },
    ('庚', '子'): {  # 十一月庚金: 仍取丁甲, 次取丙火照暖
        'candidates': [('丁', 1), ('甲', 2), ('丙', 3)],
        'evidence_refs': ['QTBJ-072-001'],
    },
    ('庚', '丑'): {  # 十二月庚金: 先取丙火解冻, 次取丁火炼金
        'candidates': [('丙', 1), ('丁', 2), ('甲', 3)],
        'evidence_refs': ['QTBJ-073-001'],
    },
    ('辛', '寅'): {  # 正月辛金: 取己土为身之本, 次用壬水淘洗
        'candidates': [('己', 1), ('壬', 2)],
        'evidence_refs': ['QTBJ-074-002'],
    },
    ('辛', '卯'): {  # 二月辛金: 壬水为尊, 得甲制伏
        'candidates': [('壬', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-075-001'],
    },
    ('辛', '辰'): {  # 三月辛金: 先壬後甲
        'candidates': [('壬', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-076-001'],
    },
    ('辛', '巳'): {  # 四月辛金: 喜壬水之洗淘, 有木制戊
        'candidates': [('壬', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-077-001'],
    },
    ('辛', '午'): {  # 五月辛金: 须己壬兼用, 壬己并用
        'candidates': [('壬', 1), ('己', 2)],
        'evidence_refs': ['QTBJ-078-001'],
    },
    ('辛', '未'): {  # 六月辛金: 先用壬水, 取庚佐之
        'candidates': [('壬', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-079-001'],
    },
    ('辛', '申'): {  # 七月辛金: 壬水居申为官清正
        'candidates': [('壬', 1)],
        'evidence_refs': ['QTBJ-080-001'],
    },
    ('辛', '酉'): {  # 八月辛金: 专用壬水淘洗, 见甲制土
        'candidates': [('壬', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-081-001'],
    },
    ('辛', '戌'): {  # 九月辛金: 先壬後甲
        'candidates': [('壬', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-082-001'],
    },
    ('辛', '亥'): {  # 十月辛金: 先用壬水, 次取丙火
        'candidates': [('壬', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-083-001'],
    },
    ('辛', '子'): {  # 十一月辛金: 壬丙两透
        'candidates': [('丙', 1), ('壬', 2)],
        'evidence_refs': ['QTBJ-084-002'],
    },
    ('辛', '丑'): {  # 十二月辛金: 先丙後壬
        'candidates': [('丙', 1), ('壬', 2)],
        'evidence_refs': ['QTBJ-085-001'],
    },
    ('壬', '寅'): {  # 正月壬水: 宜用庚金之源, 庚丙戊三者齐透
        'candidates': [('庚', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-087-001'],
    },
    ('壬', '卯'): {  # 二月壬水: 先戊後辛, 庚金次之
        'candidates': [('戊', 1), ('辛', 2), ('庚', 3)],
        'evidence_refs': ['QTBJ-088-002'],
    },
    ('壬', '辰'): {  # 三月壬水: 先用甲疏季土, 次取庚金
        'candidates': [('甲', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-089-001'],
    },
    ('壬', '巳'): {  # 四月壬水: 专取壬水比肩为助, 次取辛金发源, 庚金为佐
        'candidates': [('壬', 1), ('辛', 2), ('庚', 3)],
        'evidence_refs': ['QTBJ-090-001'],
    },
    ('壬', '午'): {  # 五月壬水: 取癸为用, 取庚为佐
        'candidates': [('庚', 1), ('癸', 2)],
        'evidence_refs': ['QTBJ-091-001'],
    },
    ('壬', '未'): {  # 六月壬水: 先辛後甲, 次取癸水
        'candidates': [('辛', 1), ('甲', 2), ('癸', 3)],
        'evidence_refs': ['QTBJ-092-001'],
    },
    ('壬', '申'): {  # 七月壬水: 专用戊土, 次取丁火
        'candidates': [('戊', 1), ('丁', 2)],
        'evidence_refs': ['QTBJ-093-001'],
    },
    ('壬', '酉'): {  # 八月壬水: 专用甲木, 庚金次之
        'candidates': [('甲', 1), ('庚', 2)],
        'evidence_refs': ['QTBJ-094-001'],
    },
    ('壬', '戌'): {  # 九月壬水: 见一甲制戌中之戊, 斯用丙火
        'candidates': [('甲', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-095-002'],
    },
    ('壬', '亥'): {  # 十月壬水: 取戊为用, 须庚制甲
        'candidates': [('戊', 1), ('丙', 2), ('庚', 3)],
        'evidence_refs': ['QTBJ-096-001'],
    },
    ('壬', '子'): {  # 十一月壬水: 先取戊土, 次用丙火
        'candidates': [('戊', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-097-001'],
    },
    ('壬', '丑'): {  # 十二月壬水: 专用丙火, 甲木佐之
        'candidates': [('丙', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-098-002'],
    },
    ('癸', '寅'): {  # 正月癸水: 先用辛金, 次用丙火照暖
        'candidates': [('辛', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-099-001'],
    },
    ('癸', '卯'): {  # 二月癸水: 专用庚金, 辛金次之, 无丁出干者贵
        'candidates': [('庚', 1), ('辛', 2)],
        'evidence_refs': ['QTBJ-100-001'],
    },
    ('癸', '辰'): {  # 三月癸水: 清明後专用丙, 谷雨後尚宜辛甲佐之
        'candidates': [('丙', 1), ('辛', 2)],
        'evidence_refs': ['QTBJ-101-001'],
    },
    ('癸', '巳'): {  # 四月癸水: 喜辛金为用, 无辛用庚, 丁破格
        'candidates': [('辛', 1)],
        'evidence_refs': ['QTBJ-102-001'],
    },
    ('癸', '午'): {  # 五月癸水: 必须庚辛为生身之本
        'candidates': [('庚', 1), ('辛', 2)],
        'evidence_refs': ['QTBJ-103-001'],
    },
    ('癸', '未'): {  # 六月癸水: 下半月庚辛有气
        'candidates': [('庚', 1), ('辛', 2)],
        'evidence_refs': ['QTBJ-104-001'],
    },
    ('癸', '申'): {  # 七月癸水: 庚司令刚锐极, 必取丁火制之
        'candidates': [('丁', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-105-001'],
    },
    ('癸', '酉'): {  # 八月癸水: 取辛金为用, 丙火佐之
        'candidates': [('辛', 1), ('丙', 2)],
        'evidence_refs': ['QTBJ-106-001'],
    },
    ('癸', '戌'): {  # 九月癸水: 专用辛金发水之源, 要比肩滋甲制戊
        'candidates': [('辛', 1), ('甲', 2)],
        'evidence_refs': ['QTBJ-107-001'],
    },
    ('癸', '亥'): {  # 十月癸水: 宜用庚辛为妙
        'candidates': [('庚', 1), ('辛', 2)],
        'evidence_refs': ['QTBJ-108-001'],
    },
    ('癸', '子'): {  # 十一月癸水: 专用丙火解冻, 又要辛金滋扶
        'candidates': [('丙', 1), ('辛', 2)],
        'evidence_refs': ['QTBJ-109-001'],
    },
    ('癸', '丑'): {  # 十二月癸水: 宜丙火解冻, 加以壬透支中多戊
        'candidates': [('丙', 1)],
        'evidence_refs': ['QTBJ-110-001'],
    },
}

def build_climate_candidates(facts: Dict[str, Any],
                             external_table: Optional[Dict[str, Any]] = None
                             ) -> Dict[str, Any]:
    """只读查表: 日干×月令 -> 调候候选干+次序。不判透出/富贵/从化/岁运。

    external_table: 可选外部调候表, 须与内置 _CLIMATE_TABLE 同构
        (key=(日干,月令), value 含 candidates/evidence_refs);
        给了则用外部表, None 时用内置表(默认行为不变)。
    """
    dm = facts['day_stem']
    mb = facts['month_branch']
    table = external_table or _CLIMATE_TABLE
    row = table.get((dm, mb))

    out = {
        'module': 'QTBJ_CLIMATE_VIEW',
        'patch': 'P160-QTBJ-CLIMATE-2',
        # 冲突命名空间归属(对齐 namespace_registry PATCH-023C): 防跨领域串规则
        'namespace': 'QTBJ.climate_use',
        'namespace_type': 'climate',
        'day_master': dm,
        'month_branch': mb,
        'climate_candidates': [],
        'candidate_count': 0,
        'judgment_status': 'CLIMATE_CANDIDATE_ONLY',
        'boundary_note': (
            '仅《穷通宝鉴》日干×月令原文所载调候干及先后次序的查表投影; '
            'order 为原文次序非评分; 并列不裁, 不 selected; 不判断调候干透出/得用; '
            '不录富贵/岁运喜忌/从化/降级; 与 PZZQ 格局用神独立 namespace, 不混为总用神; '
            '未录入条目返回 NOT_REGISTERED, 不补全不编造; 不接 production_entry'
        ),
        'evidence_refs': [],
    }

    if row is None:
        out['state'] = 'NOT_REGISTERED'
        out['note'] = '该日干月令调候未在本表录入, 待逐条原文补录'
        return out

    cands: List[Dict[str, Any]] = []
    for stem, order in row['candidates']:
        cands.append({
            'candidate_id': 'CL-%s-%s-%s-%d' % (dm, mb, stem, order),
            'stem': stem,
            'order': order,                 # 原文先后次序, 非权重
            'evidence_refs': list(row['evidence_refs']),
            'status': 'CANDIDATE',
        })
    # 按原文次序排列(表内已排)
    cands.sort(key=lambda c: c['order'])
    out['climate_candidates'] = cands
    out['candidate_count'] = len(cands)
    out['state'] = 'REGISTERED'
    out['evidence_refs'] = list(row['evidence_refs'])
    return out
