# -*- coding: utf-8 -*-
"""
Qintian Evidence Bindings — 钦天门证据等级与一手源（Z44 蔡明宏主源版）

严格工程边界：
- 每条规则绑定 grade=1 一手源（蔡明宏《悟我十八年》OCR 原文）
- 铁律：原著古书原文为准，不采今人推测口径
- Z44 主源切换：许铨仁/四余独步规则全部清除（书不在 D 盘，无法溯源），
  唯一北派主源 = 蔡明宏《悟我十八年》（正文完整 + PDF 原件在）

60 条 production（grade 1×58 / 3×2，蔡明宏原文；Z80-G 实测校准）：
  - QTN-CMB-001 来因宫 = 生年干所在宫位（"太极引用在斗数上即来因宫"）
  - QTN-CMB-002 生年四化=空间(体) / 自化=时间(用)
  - QTN-CMB-004 向心自化（箭头向内，物质的凝聚）
  - QTN-CMB-006 串联自化（同向自化串联）
  - QTN-CMB-007 离心自化（箭头向外，物质的分散）
  - QTN-CMB-011 自化五分类（生年有/无自化 × 飞宫遇/不遇）
  - QTN-CMB-012 出与入（自化面对生年四化的出入）
  - QTN-CMB-013 法象（自化之象对照生年四化宫位）

已清除（许铨仁/四余独步时代的旧编号内容，主源切换后无效）：
  - 003 立太极 / 005 忌入六亲=亏欠 / 008 十二宫逐宫详释
  - 009 子/丑不做来因宫 / 010 化忌多变动
Z65 空编号重分配（以蔡明宏《悟我十八年》自化篇原文为准）：
  - 003 自化本义（引言） / 005 自化理象气数（导读）
  - 008 自化次序（生年忌再自化禄） / 009 自化理体论
  - 010 自化基本分类（单星/双星/串联/纯自化）

所有 production 规则 evidence_grade=1（一手原文）。
"""

from __future__ import annotations

from typing import Dict, NamedTuple


class QintianEvidence(NamedTuple):
    """钦天门证据 binding (NamedTuple 保持 immutable)"""
    rule_id: str
    title: str
    verbatim_quote: str
    source: str
    source_url: str
    grade: int  # 1=蔡明宏《悟我十八年》原文 2=传承整理 3=后人整理 4=推演
    evidence_type: str  # PRIMARY_TRADITION / SYSTEMATIZED / CANDIDATE


EVIDENCE_BINDINGS: Dict[str, QintianEvidence] = {
    "QTN-CMB-003": QintianEvidence(
        rule_id="QTN-CMB-003",
        title="自化本义（引言·平衡原理/无为而自化/时空效应）",
        verbatim_quote="自化，所謂自化，是指一件事物現象本俱該有的平衡原理，就像五行，不能太過或不及一般。太過與不及就失去了它的平衡性，導致於出現了一件事物的吉或凶。……它是應時間（不論大限或流年）而發生的。故它是無為的，自然而形成的，故曰：「無為而自化」。……自化強調於時空效應法則。是一種事物變化的自然規律。",
        source="蔡明宏《紫微斗數悟我十八年》自化篇·單元一 引言（OCR最終版，453-454頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-005": QintianEvidence(
        rule_id="QTN-CMB-005",
        title="自化理象气数（四导读：理=平衡原理/象=时空出入/数=变化论/气=时间存有论）",
        verbatim_quote="就自化來說「理」——根本就是指宇宙萬有現象的平衡原理。……太極若引用在斗數上，所指的就是來因宮。……就自化來說「象」——約而言之，就是現象有時空的出入。……就自化來說「數」——現象存在的另一種變化論。……就自化來說「氣」——在表達時間上的種種不同物相的存有論。",
        source="蔡明宏《紫微斗數悟我十八年》自化篇·單元二 導讀（OCR最終版，459-461頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-008": QintianEvidence(
        rule_id="QTN-CMB-008",
        title="自化次序（生年忌再自化禄：由少到多之量）",
        verbatim_quote="做一個舉例：生年忌 再 自化祿。解：化忌主冬天，自化了祿，那好比今年冬天的植物，到明年秋天收成，這就是次序。……生年忌在財，本是勞碌或上班的安定薪俸財。但因為化忌，再自化祿，代表會由少到多的「量」。",
        source="蔡明宏《紫微斗數悟我十八年》自化篇·單元二 自化詮釋 + 單元三 應用（OCR最終版，463/465頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-009": QintianEvidence(
        rule_id="QTN-CMB-009",
        title="自化理体论（生年四化=理体/自化=用/自化皆法象生年四化）",
        verbatim_quote="生年四化，就是「理」的本體存在論。生年又自化，就是自化的「用」，在「體」上發生了種種情況的變化，若沒有一個本體在先（物相在先），自化就不存在任何意義。……自化的「象」，都要「法象」到生年四化上去，再由宮位上判斷現象的吉凶禍福！",
        source="蔡明宏《紫微斗數悟我十八年》自化篇·單元三 詮釋(一) 自化在理上而言（OCR最終版，464頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-010": QintianEvidence(
        rule_id="QTN-CMB-010",
        title="自化基本分类（单星/双星/串联/纯自化；来因宫自化另解）",
        verbatim_quote="它基本的分類如下：第一、生年單星自化。第二、生年雙星自化。第三、生年四化，自化又串聯。第四、無生年四化，但有自化——並串聯。註：來因宮自化者，請見來因宮專解。（不在此限）",
        source="蔡明宏《紫微斗數悟我十八年》自化篇·單元三（OCR最終版，465頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-034": QintianEvidence(
        rule_id="QTN-CMB-034",
        title="五行局论断（南/北派共用部分）",
        verbatim_quote="水二局，根气属阴，性善感，思绪不息，善于体察人情；气无定形，环境极易牵引其心性。喜静守以蓄气，若常年动荡，则思虑耗散，多内扰。……木三局，阳根，主生长舒展，重情义，喜向外拓展，贵人缘重。……金四局，阴肃之气，守原则，明取舍，做事果决，重条理。……土五局，中和之气，能纳万物，包容厚重，耐得住辛劳。……火六局，阳烈之气，主发扬，有冲劲，喜舞台展示，做事爆发力强。",
        source="陆斌兆《紫微斗数讲义：星曜性质》王亭之注解（复旦大学出版社）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-035": QintianEvidence(
        rule_id="QTN-CMB-035",
        title="五行局×身宫论断（身宫落六寄宫；非六寄宫无论断）",
        verbatim_quote="水二局身同命。先天根气善感，后天心性与先天本貌合一。……身落财帛：后半生心念多系于生计财利，求财思路灵动，善随势应变。……（5局×6寄宫，陆斌兆原讲义无现成原文，依据该体系立论撰写，同体系配套文本）",
        source="陆斌兆《紫微斗数讲义》体系延伸（derived_commentary，用户提供，grade=3）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系",
        grade=3,
        evidence_type="SYSTEMATIZED",
    ),
    "QTN-CMB-031": QintianEvidence(
        rule_id="QTN-CMB-031",
        title="四化象义（季节/天地人物/分组）",
        verbatim_quote="化科：春天是萬物萌生，百花盛開的季節。化權：夏天是水果豐盛，水中弄潮的季節。化祿：秋天是穀穗飄香，五穀豐收的季節。化忌：冬天是銀裝素裹，闔家團聚的季節。……四化相應天、地、人、物｜象徵天祿、地權、人科、物忌……化科、化權一組（木、火一家）；化祿、化忌一組（金、水同航）。",
        source="蔡明宏《紫微斗數悟我十八年》第四章·關注你生命的眼神（OCR最終版，421-424頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-032": QintianEvidence(
        rule_id="QTN-CMB-032",
        title="财帛宫飞化论断（入/照/冲本命三合）",
        verbatim_quote="財帛｜代表一個人的賺錢能力，又名賺錢宮。祿、權、科入本命三合，是自立謀生，貴中之財。祿、權、科照本命三合，亦是自立謀生，為其照三合之賺錢能力大於入三合。(三)化忌宜入本命三合，為吉，不宜沖三合，為凶，則以上班薪俸為宜。",
        source="蔡明宏《紫微斗數飛星秘儀》四化宮位變通淺釋·財帛（OCR完整版，33-34頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-033": QintianEvidence(
        rule_id="QTN-CMB-033",
        title="官禄宫飞化论断（入/照/冲本命三合）",
        verbatim_quote="官祿｜代表一個人的事業狀況，為之事業宮，又名求學宮。(一)祿、權、科入三合，是自立謀生、事業順利。(二)祿、權、科照三合，亦主自立謀生，事業順利並多方面發展，唯其照三合之事發展大於入三合。(三)化忌星宜入三合，為吉，穩定，但薪俸者並不代表升遷。化忌星不宜沖三合，沖者為凶，且不穩定，變動多。",
        source="蔡明宏《紫微斗數飛星秘儀》四化宮位變通淺釋·官祿（OCR完整版，34頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-029": QintianEvidence(
        rule_id="QTN-CMB-029",
        title="大限六亲宫忌冲本命六亲（缘薄/对待不佳）",
        verbatim_quote="大限六親宮化忌不宜沖本命之某六親宮，是主某六親對某六親緣份薄或對待不佳。例：大限兄弟宮化忌沖本命父母宮，代表此大限兄弟與父母間，對待不會良佳，口角難免。理則：即「用」不可沖「體」，若祿、權、科者照體則為佳論。",
        source="蔡明宏《紫微斗數飛星秘儀》基本活盤觀念（OCR完整版，70頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-030": QintianEvidence(
        rule_id="QTN-CMB-030",
        title="命格自化损格（三方见禄权科 + 所落宫自化 → 贵达不显）",
        verbatim_quote="命格解：用生年四化，三方見祿、權、科、主貴，唯其所落祿、權、科之宮位，均有「自化」，則貴中有損其格，便成貴達不顯。",
        source="蔡明宏《紫微斗數飛星秘儀》命例解·命格解（OCR完整版，72頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-028": QintianEvidence(
        rule_id="QTN-CMB-028",
        title="十干化曜浅释（生年四化逐星论断）",
        verbatim_quote="一甲干：廉貞化祿：主地位高升，名氣揚，電腦生意好，外貿生意佳，有意外不勞而獲之財。破軍化權：主多變動、財富橫發、偏財運強……太陽化忌：不利男性、父、夫、子，眼目有疾……六癸干：破軍化祿：代表富足、衣食不缺……貪狼化忌：小心因桃花而惹禍，主破財，官非，與食色有關。",
        source="蔡明宏《紫微斗數飛星秘儀》十干化曜淺釋（OCR完整版，73-77頁）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-025": QintianEvidence(
        rule_id="QTN-CMB-025",
        title="田宅宫飞化论断（住宅环境/祖产财源/驿马/置产）",
        verbatim_quote="田宅宮：稱之為不動產宮，包括祖業在內，亦名家運宮、財庫宮、環境宮。（一）田宅宮飛化之四化在田宅三合，可見住宅附近之環境，有物相應。（二）田宅宮飛化之四化在本命三合，可見祖產有無及財源應用，包括照命三合。（三）田宅宮飛化之四化，在遷移、子女，代表驛馬。（四）命、財、官飛化入田宅，可見有無增置不動產。",
        source="蔡明宏《紫微斗數飛星秘儀》四化宮位變通淺釋·田宅宮（OCR完整版）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-026": QintianEvidence(
        rule_id="QTN-CMB-026",
        title="六阳宫主贵六阴宫主富（三吉化落宫贵富取向；全落六阴主财利之格、于六阴需人和）",
        verbatim_quote="六陽宮主貴，六陰宮主富。……命宮三合不見生年祿權科而命宮自坐生年忌，主白手起家，貴達難顯，以上班或技術為生計。然生年祿權科分別在六陰位，表示此人會有錢（有無錢要有時運），以財富為主，偏向財利之格；時運來臨則財多勝貴之質。……三吉化於六陰者，要成就的基本條件，是「人和」，若失人和，就註定失敗的命運步伐……得有人和者，財利亦隨之而來，是人蔭其成，而非本身之獨成。",
        source="蔡明宏《紫微斗數飛星秘儀》四化宮位變通淺釋·命宮 / 宮位論斷（OCR完整版，对照 vr-d.com 原著 PDF 全文补证财利之格）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-027": QintianEvidence(
        rule_id="QTN-CMB-027",
        title="来因宫定贵格自立/借力（三方见禄权科 + 来因宫财帛/兄弟）",
        verbatim_quote="某甲之命盤三方有祿、權、科——主貴。……某甲生年干若與財帛同宮，則其人之貴靠自己，不需借他人之助，代表可自立獨謀之格。……某乙生年干若與兄弟同宮，則其人之貴非靠自己，而需借朋友或兄弟之協，方可助其貴，否則生年四化在三方見，亦無用於濟事。便成一種假象。",
        source="蔡明宏《紫微斗數飛星秘儀》四化活盤應用（OCR完整版）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-023": QintianEvidence(
        rule_id="QTN-CMB-023",
        title="命宫干飞化论贵格（三合入/照/冲）",
        verbatim_quote="命宮代表一個人的命格高低，以命宮干四化顯示命格的高低。……祿、權、科落在本命三合，主貴格，並主自立更生。祿、權、科落在其餘三宮（夫、遷、福），為之照，亦主貴，但須借他人之助，方易成功。化忌入本命三合，不失其格，唯其能力表現易犯小人干擾，阻礙多；化忌入其餘三宮，謂之沖三合，則損貴中之格，易變初衷志向。化忌沖三合者，薪俸者為宜。",
        source="蔡明宏《紫微斗數飛星秘儀》四化宮位變通淺釋·命宮（OCR完整版）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-024": QintianEvidence(
        rule_id="QTN-CMB-024",
        title="六亲宫忌入忌冲（谁化忌冲谁缘薄，谁化忌入谁口角）",
        verbatim_quote="六親宮：命宮、兄弟、夫妻、子女、交友、父母，謂之六親宮。凡六親之宮位，誰化忌沖誰，均主緣薄。誰化忌入誰之宮位，雖不佳，但比沖吉，只可解口角意見多。",
        source="蔡明宏《紫微斗數飛星秘儀》四化宮位變通淺釋·六親宮（OCR完整版）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\飞星秘仪\飞星秘仪_OCR完整版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-022": QintianEvidence(
        rule_id="QTN-CMB-022",
        title="四化现象平衡原理（生年单象/双象 vs 自化，单对单、双对双）",
        verbatim_quote="平衡的定理，是針對「生年四化」而言。生年四化有單象與雙象之別，平衡其理，一定要單對單，雙對雙。把同類的歸類並兼看「宮位」，成現象的相對論。……（例）廉貞化祿在兄弟，代表有兄弟。廉貞化祿，又自化忌。（單星自化）把自化的化忌，去法生年忌。……（例）福德坐癸又自化科，但生年科、忌是雙象在官祿宮，所以把自化科法回生年科，一定還少一顆化忌，否則不會平衡。",
        source="蔡明宏《悟我十八年》第四章 自化應用篇·詮釋（一）自化在「理」上而言（OCR最终版）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-020": QintianEvidence(
        rule_id="QTN-CMB-020",
        title="用神法则（禄忌一组 / 权科一组；权科用神必须配合忌）",
        verbatim_quote="用神：祿、忌一組 權、科一組 但，權、科用神，必須配合忌。……凡是來因宮自化者，其命盤論命方式都要由「來因宮」做論命的緣起，並看來因宮的四化是什麼「象」，分出用神。用神的要領：就是祿～忌一組 權～科一組。……（例）壬年生，來因宮自化在命宮，紫微權自化權，其用神就是權科組（優先次序）。……權、科用神的媒介一定要有化忌。",
        source="蔡明宏《悟我十八年》第五章 論命須知·四化圖 / 命例一（OCR最终版）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-021": QintianEvidence(
        rule_id="QTN-CMB-021",
        title="十二宫位阴阳表里（六阳六阴 / 一阴一阳相为表里 / 对宫同断）",
        verbatim_quote="十二宮位，分六陽、六陰，猶卦有六爻之辯。……（表）陽：命/夫妻/財帛/遷移/事業/福德；陰：兄弟/子女/疾厄/交友/田宅/父母。……（一陰一陽相為表裡圖）田宅官祿交友遷移／福德疾厄／父母財帛／命宮兄弟夫妻子女。……命宮化忌入遷移，有驛馬在外之命或遷移化忌入命宮，解釋也是一樣。",
        source="蔡明宏《悟我十八年》第三章 細說十二宮位（OCR最终版）",
        source_url=r"D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\OCR转录版本\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-001": QintianEvidence(
        rule_id="QTN-CMB-001",
        title="来因宫 = 生年干所在宫位",
        verbatim_quote="太极若引用在斗数上，所指的就是来因宫。（即宫位与出生的天干相同的宫位）。例 甲年生，甲在命盘的田宅宫，则田宅宫叫做来因宫。所以每个人于命盘都有来因宫，都有他自己的「太极」。",
        source="蔡明宏《悟我十八年》第四章 自化篇·单元二 导读（理）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-002": QintianEvidence(
        rule_id="QTN-CMB-002",
        title="生年四化=空间(体) / 自化=时间(用)",
        verbatim_quote="生年的象，是空间性的，叫做物的存在论。自化的象，是时间性的，叫做物的存在论。生年四化，就先有物（体）；生年四化又自化，是在已有之物后（体），再产生另一种变化（用），体用合一。",
        source="蔡明宏《悟我十八年》第四章 自化篇·单元一 引言 / 单元二 导读（气）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-004": QintianEvidence(
        rule_id="QTN-CMB-004",
        title="向心自化（箭头向内，物质的凝聚）",
        verbatim_quote="自化的游戏规则：向心力与离心力两种。箭头向内（向心力）。向心力→物质的凝聚。",
        source="蔡明宏《悟我十八年》第四章 自化篇·单元一 引言（自化的游戏规则）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-006": QintianEvidence(
        rule_id="QTN-CMB-006",
        title="串联自化",
        verbatim_quote="自化的游戏规则：（3）串联与不串联。飞宫不遇生年四化，但有自化者（并串联）。",
        source="蔡明宏《悟我十八年》第四章 自化篇·单元一 引言 / 单元三 应用篇",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-007": QintianEvidence(
        rule_id="QTN-CMB-007",
        title="离心自化（箭头向外，物质的分散）",
        verbatim_quote="自化的游戏规则：向心力与离心力两种。箭头向外（离心力）。离心力→物质的分散。把已有的事物现象变成没有 或改变另一种模式。",
        source="蔡明宏《悟我十八年》第四章 自化篇·单元一 引言（自化的游戏规则）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-011": QintianEvidence(
        rule_id="QTN-CMB-011",
        title="自化五分类",
        verbatim_quote="（一）生年四化，有自化者。（包括来因宫本身自己有自化者）（二）生年四化，没有自化者。（三）无生年四化，有自化者。（四）飞宫遇生年四化，又有自化者。（五）飞宫不遇生年四化，但有自化者。（六）飞宫不遇生年四化，但有自化者。（并串联）。以上是现象的组合性。",
        source="蔡明宏《悟我十八年》第四章 自化篇·单元一 引言",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-012": QintianEvidence(
        rule_id="QTN-CMB-012",
        title="出与入",
        verbatim_quote="站在太阴化禄的流年（酉宫）去面对巨门的自化禄是'入'。站在巨门的自化禄去面对太阴的化禄是'出'。",
        source="蔡明宏《悟我十八年》第四章 自化篇·单元一 引言（出与入的区分）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-013": QintianEvidence(
        rule_id="QTN-CMB-013",
        title="法象（自化之象对照生年四化）",
        verbatim_quote="何谓「法象」，就是把自化的'象'（看是禄、权、科、忌的那一种），再去对照生年四化的宫位，然后依两宫位互动，就产生了现象与物相及吉或凶的征兆。",
        source="蔡明宏《悟我十八年》第四章 自化篇·单元三 应用篇（法象）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-014": QintianEvidence(
        rule_id="QTN-CMB-014",
        title="北派身宫论断（命为体身为用）",
        verbatim_quote="命为体，身为用。命是先天带来之根，身是此生要去完成的果。身宫，是你这一辈子「放不下、不断追求」的那一宫。",
        source="北派钦天体系延伸（蔡明宏《悟我十八年》体系，derived_commentary）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\蔡明宏_紫微斗数_悟我十八年_OCR_最终版.txt",
        grade=3,
        evidence_type="SYSTEMATIZED",
    ),
    "QTN-CMB-019": QintianEvidence(
        rule_id="QTN-CMB-019",
        title="生年斗君入十二宫解（十二宫以六宫论）",
        verbatim_quote="一、生年斗君在命宮，一生中的言行，一舉一動與自己脫離不了關係……◎記住！十二宮以六宮論如下：命宮為100%|遷移宮則為70%。兄弟宮為100%|交友宮則為70%。夫妻宮為100%|官祿宮則為70%。子女宮為100%|田宅宮則為70%。財帛宮為100%|福德宮則為70%。疾厄宮為100%|父母宮則為70%。",
        source="蔡明宏《紫微斗數飛星秘儀》「生年斗君入十二宮解」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-018": QintianEvidence(
        rule_id="QTN-CMB-018",
        title="自化浅解（取意托乎随心而化乃名自化；自化反其意）",
        verbatim_quote="秘儀有載：「取意託乎，隨心而化，乃名自化」，為自化之解。凡在四化中，不論四化如何飛化，或與生年四化碰撞產生的各種情況，若逢該宮自化時，其意則全變，不可拘泥於原本之意。自化有反其「意」之作用。本為不好的，也許因自化而好，也有本為不好，因自化而惡化。更有本是好的，因自化而更好，也有本是好的，因自化而變壞。",
        source="蔡明宏《紫微斗數飛星秘儀》「四化自化淺解」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-017": QintianEvidence(
        rule_id="QTN-CMB-017",
        title="大限四化应用（一律与本命息息相关，本命盘宫干为用）",
        verbatim_quote="大限的應用，一律與本命息息相關。當任何宮位為飛化定點時，均與生年四化發生關係。用大限財帛言，則用命盤之「丙」干飛化；化祿照大限官祿，可是逢到生年忌，則構成祿忌，成為雙忌論。",
        source="蔡明宏《紫微斗數飛星秘儀》「大限四化應用」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-016": QintianEvidence(
        rule_id="QTN-CMB-016",
        title="流年四化应用（以本命盘原始宫干为主，不以流年干）",
        verbatim_quote="理：流年者即太歲也。每逢一年順行一宮，例今年為乙丑年，則以地支丑位為太歲位。四化運用不以小限為主。太歲使用分兩種（一）四化以本命盤原始宮干為主。（二）以流年干為主。二者均有使用，唯飛星秘儀記載用本命盤之宮干為主。例：原命盤地支丑位為癸丑，則流年用「癸」一飛化，不以今年流年乙丑之「乙」為飛化。若用乙，則每個人今年均太陰化忌。",
        source="蔡明宏《紫微斗數飛星秘儀》「流年四化應用」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-015": QintianEvidence(
        rule_id="QTN-CMB-015",
        title="生年四化在十二宫之解义（单象解）",
        verbatim_quote="(1) 命宮：化祿：聰明、自立、人緣佳、衣食不缺、解厄之功。化權：自視高、任性、霸權、機智、能力才幹型、不易接受別人意見、主觀強。化忌：坎坷不順、固執己見、易犯小人。化科：清秀、人緣佳、好學藝、解厄之功、助人為樂。……註：本段註解以生年四化在十二宮之解釋，全以單象而解。",
        source="蔡明宏《紫微斗數飛星秘儀》「生年四化在十二宮之解義」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-036": QintianEvidence(
        rule_id="QTN-CMB-036",
        title="财帛宫坐生年化忌（财格压制）",
        verbatim_quote="財帛宮化忌顯示不吉之象，則祿、權、科，同時顯示不吉利解，化忌凶時，三吉化亦凶，化忌為吉時，三吉化亦吉。",
        source="蔡明宏《紫微斗數飛星秘儀》「财帛宫四化应用·化忌论断」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-037": QintianEvidence(
        rule_id="QTN-CMB-037",
        title="财帛宫坐生年禄权科（财格显象）",
        verbatim_quote="（5）財帛：化祿：①能自立謀生。②自創業賺錢。③忙碌。①不善理財。化權：①善於用錢創業。②不存死錢利於週轉活用。……（四）化科在財帛宮，代表以上班宜，且安定不善變動。並更主此人貴人相助良多。",
        source="蔡明宏《紫微斗數飛星秘儀》「财帛宫四化应用」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-038": QintianEvidence(
        rule_id="QTN-CMB-038",
        title="夫妻宫坐凶星（婚姻凶象）",
        verbatim_quote="①破軍星在夫妻宮、子女宮，容易有失的一面，即意味著留不住，耗損現象。①巨門星入六親宮，代表排斥性較強，象徵遺棄星……在夫妻宮宜晚婚為佳。①地空星與地劫星在夫妻宮……使婚姻難以成局。①天梁星的缺點：宜改老大之作風，防婚姻與感情問題，因本身格局高之故也。",
        source="蔡明宏《紫微斗數飛星秘儀》「星曜论·破军/巨门/地空地劫」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-039": QintianEvidence(
        rule_id="QTN-CMB-039",
        title="生年化忌坐夫妻宫（婚姻波折）",
        verbatim_quote="化忌在夫妻：忌星在六親宮，代表虧欠，即虧欠，則主此人必有太太或先生，不必為婚姻之事煩惱。唯不宜太早婚，婚前會有波折。",
        source="蔡明宏《紫微斗數飛星秘儀》「生年四化在十二宮之解義·夫妻宮」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-040": QintianEvidence(
        rule_id="QTN-CMB-040",
        title="贵格见四煞（格高受折）",
        verbatim_quote="紫微化科：名聲遠揚，貴人提拔，地位高升，若見四煞星，升遷受挫，破財招損，尊星化科較重面子。……①左輔星與右弼星三合會巨門星、天機星、七殺星、四煞星等，主命格較低。",
        source="蔡明宏《紫微斗數飛星秘儀》「四化论断·紫微化科」「星曜论·左辅右弼」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-041": QintianEvidence(
        rule_id="QTN-CMB-041",
        title="灾煞星血光论断（命/疾厄/迁移）",
        verbatim_quote="①羊刃星……化氣為刑傷、凶厄之神，主災殺，易見血光。……①破軍星也是血光星，對本身而言，多外傷。……①太陰星……又稱為血光之星，與開刀有關。天機化忌：……代表死亡星，四肢易有外傷，或機械、車禍之事發生。廉貞化忌：……在遷移宮化忌與羊刃同宮多凶險。遇廉貞、七殺大小二限重逢，小心車禍。",
        source="蔡明宏《紫微斗數飛星秘儀》「星曜论·羊刃/破军/太阴」（OCR校对版，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-042": QintianEvidence(
        rule_id="QTN-CMB-042",
        title="空宫双忌论（四化宫位变通·四象法）",
        verbatim_quote="(二)四象法：宫位无主星，不借对宫之星为用，以本无主星之宫位的宫干为四化飞化要诀，以象其宫位之吉凶。……命宫在申无主星，对宫寅有太阳、巨门同宫，若命宫干为甲，则太阳化忌在对宫，便成双忌论，力量加倍。因命宫无主星之故。假若，甲干不在命宫，而在迁移宫与太阳、巨门同宫位，则太阳化忌为单化忌。以此类推，凡无主星之宫位皆同。",
        source="蔡明宏《紫微斗數飛星秘儀》「四化宫位变通浅释(一)」（OCR校对版第33页，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-043": QintianEvidence(
        rule_id="QTN-CMB-043",
        title="化忌在命又化忌（难贵显·格局中上层以下）",
        verbatim_quote="（四）化忌在命，又化忌，難貴顯，格局難在中上層面，縱任有財，層面不變。",
        source="蔡明宏《紫微斗數飛星秘儀》「四化宫位变通·命宫论断」（OCR校对版第55页，对照 vr-d.com 原著 PDF 校验）",
        source_url="D:\\顺天系统资料\\豆包资料\\六部经典校对版\\紫薇体系\\OCR转录版本\\飞星秘仪\\飞星秘仪_OCR校对版.txt",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-044": QintianEvidence(
        rule_id="QTN-CMB-044",
        title="双象论（生年四化两星同宫六种组合论断）",
        verbatim_quote="祿忌：祿不可解忌，以雙忌論，主凶。祿權：財利、發達、吉祥、名利雙收（利大於名）。祿科：名揚、才幹、獲利、長壽、名利雙收（名大於利）。權科：名利得，以專技才藝為主，不可自愎太過。權忌：以技能或薪俸為主，先忌後權，倍加辛勞。科忌：以學術或手藝為主，先忌後得助。勿太自信反敗。",
        source="蔡明宏《紫微斗數飛星秘儀》「四化应用入门篇」（vr-d.com 原著 PDF 全文）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-045": QintianEvidence(
        rule_id="QTN-CMB-045",
        title="命宫宫干=生年干（四化双倍函义·为臣不为君格）",
        verbatim_quote="命宮宮干爲甲，與生年甲同樣的四化，顯示雙倍之函義，故吉凶成敗，有強烈分明之別。忌星坐命，上班爲宜，又宮干坐甲，太陽又化忌，可謂爲臣不爲君之格，若強而爲君格，終究必敗，宜幕後之使者。",
        source="蔡明宏《紫微斗數飛星秘儀》「命格解」（vr-d.com 原著 PDF 全文）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-046": QintianEvidence(
        rule_id="QTN-CMB-046",
        title="命宫坐生年忌+三合不见三吉化（白手起家·贵达难显）",
        verbatim_quote="命宮三合不見生年祿、權、科，而命宮自坐生年忌，主白手起家。貴達難顯，以上班或技術為生計。",
        source="蔡明宏《紫微斗數飛星秘儀》「命格解」（vr-d.com 原著 PDF 全文）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-047": QintianEvidence(
        rule_id="QTN-CMB-047",
        title="结婚限（夫妻宫坐生年三吉化 → 第三大限为结婚限）",
        verbatim_quote="夫妻宮坐壬干……已象徵在此大限會結婚，不論順行或逆行者，均於第三個大限爲結婚限。",
        source="蔡明宏《紫微斗數飛星秘儀》「命例解」（vr-d.com 原著 PDF 全文）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-048": QintianEvidence(
        rule_id="QTN-CMB-048",
        title="天刑逢生年化忌 → 官非牢狱",
        verbatim_quote="天刑星代表官非與牢獄之災，尤其逢化忌時，要注意。",
        source="蔡明宏《飛星秘儀》星性解·天刑星（本地 OCR 校对版 + vr-d.com 原著 PDF）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-049": QintianEvidence(
        rule_id="QTN-CMB-049",
        title="天刑入夫妻宫 → 易离婚、宜晚婚",
        verbatim_quote="天刑星不宜入夫妻宮，容易有離婚現象，晚婚佳。",
        source="蔡明宏《飛星秘儀》星性解·天刑星",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-050": QintianEvidence(
        rule_id="QTN-CMB-050",
        title="天姚入夫妻宫 → 多艳遇（桃花）",
        verbatim_quote="天姚星在夫妻宮，夫妻雙方都有人緣，多艷遇。",
        source="蔡明宏《飛星秘儀》星性解·天姚星",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-051": QintianEvidence(
        rule_id="QTN-CMB-051",
        title="武曲化忌与天刑同宫 → 官非刑罚",
        verbatim_quote="武曲化忌：財星化忌，主財不利，周轉不靈，倒債多，與天刑同宮化忌，因官非刑罰，宜節省守財。",
        source="蔡明宏《飛星秘儀》十干化曜·己干",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-052": QintianEvidence(
        rule_id="QTN-CMB-052",
        title="太阳化忌与天刑同宫 → 牢狱之灾",
        verbatim_quote="太陽化忌：不利男性、父、夫、子、眼目有疾、近視多、有失眠、煩躁不安現象，與天刑星逢化忌，注意牢獄之災。",
        source="蔡明宏《飛星秘儀》十干化曜·庚干",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-059": QintianEvidence(
        rule_id="QTN-CMB-059",
        title="大限忌+流年忌双忌叠加（应期到年）",
        verbatim_quote="推斷流年時，通常只需視大限及流年兩組化曜。當生年四化被衝會之時，然後始須注意，不衝起則作用甚小。（中州派《紫微斗數深造講義·化曜》）；流年化忌再次落入大限化忌已在的宮位，形成「雙忌疊加」，通常代表該年需要高度留意相關事件。（starnum 四化時序啟動）；推算流年運，應由大限盤的天干四化情況並結合本命盤之象來推斷，三環相扣。（《紫微斗數精成》第14章）",
        source="中州派《紫微斗数深造讲义·化曜》（国学大师 guoxuedashi.com）+《紫微斗数精成》第14章 + starnum 四化时序启动",
        source_url="https://www.guoxuedashi.com/a/22312bxfo/281041k.html",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-060": QintianEvidence(
        rule_id="QTN-CMB-060",
        title="生年忌+大限忌+流年忌三忌同宫（高风险年）",
        verbatim_quote="若本命、大限、流年三層的忌都落在同一個宮位，就是常說的「三忌同宮」——那一年那一宮代表的事情需要優先留意。（starnum 宫干四化指南）；流年化忌若再次落入已有生年或大限化忌的宮位，三忌疊加，事件機率大幅提升。（starnum 化忌完整指南）",
        source="starnum《紫微宫干四化完整指南》+《四化化忌完整指南》（多源一致通行法）",
        source_url="https://starnum.com.tw/blog/zh-TW/palaces-overview-gonggan-sihua-dynamics-pillar",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-058": QintianEvidence(
        rule_id="QTN-CMB-058",
        title="辛干四化（巨门禄/太阳权/文曲科/文昌忌）",
        verbatim_quote="子女宮宮干坐「辛」巨門化祿與文昌化忌，同宮在財帛，雖言雙忌，必有子女（不論男女）……太陽化權入命宮，有子女，唯將來子女均獨立，即自立更生格，個性比較剛強……文曲化科入夫妻，代表子女會喜接近母親，得父母之寵……更也代表子女會孝順。",
        source="蔡明宏《飛星秘儀》子女宮論斷（OCR 校对版第 61-62 页，vr-d.com 原著 PDF）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-057": QintianEvidence(
        rule_id="QTN-CMB-057",
        title="流年+流月四化组合（天地人三盘）",
        verbatim_quote="本命為天──生年四化與大限錯綜，斷大限吉凶。大限為地──大限介於本命與流年之間為機紐。流年為人──生年四化與流年錯綜，斷流年吉凶。大限為天 流年為地 流月為人──亦三合而一。四化之飛曜天干，一律用本命盤天干。不可另取用。",
        source="蔡明宏《飛星秘儀》四化總結概要（vr-d.com 原著 PDF）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-056": QintianEvidence(
        rule_id="QTN-CMB-056",
        title="三吉化于六阴宫 → 成败系于人和",
        verbatim_quote="祿、權、科全在六陰位，非自立格，若要有成，必須要有人於背後輔佐，輔相，才有自立可言。三吉化於六陰者，要成就的基本條件，是「人和」，若失人和，就註定失敗的命運步伐。得有人和者，財利亦隨之而來，是人蔭其成，而非本身之獨成。",
        source="蔡明宏《飛星秘儀》三吉化于六阴（PDF书85-86页原文，OCR空表格为命盘图非文字残缺）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-054": QintianEvidence(
        rule_id="QTN-CMB-054",
        title="流月四化应用（斗君起正月，本命盘宫干飞化）",
        verbatim_quote="流月即指流年十二個月的吉凶，法流年而行。用：其用有二種。（一）斗君（二）用寅為正月始。若流年之宮干用原始宮干者，流月一律用「斗君」。流月四化飛曜天干：一律用本命盤天干，不可另取用。",
        source="蔡明宏《飛星秘儀》流月四化应用（vr-d.com 原著 PDF）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-055": QintianEvidence(
        rule_id="QTN-CMB-055",
        title="流月化忌入天刑宫 → 该月官非牢狱",
        verbatim_quote="天刑星代表官非與牢獄之災，尤其逢化忌時，要注意。／流月用斗君，四化飛曜天干一律用本命盤天干。",
        source="蔡明宏《飛星秘儀》星性解·天刑星 + 流月四化应用（vr-d.com 原著 PDF）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
    "QTN-CMB-053": QintianEvidence(
        rule_id="QTN-CMB-053",
        title="大限化忌入天刑宫 → 大限官非牢狱",
        verbatim_quote="天刑星代表官非與牢獄之災，尤其逢化忌時，要注意。／大限即以本命盤的宮干為大限之宮干。",
        source="蔡明宏《飛星秘儀》星性解·天刑星 + 大限四化应用（vr-d.com 原著 PDF）",
        source_url="https://vr-d.com/pdf-file/紫微斗数/华山钦天四化紫微斗数飞星秘仪_蔡明宏.pdf",
        grade=1,
        evidence_type="PRIMARY_TRADITION",
    ),
}

DRAFT_BINDINGS: Dict[str, QintianEvidence] = {}


def get_evidence(rule_id: str) -> QintianEvidence | None:
    """根据 rule_id 获取 evidence binding (production only)"""
    return EVIDENCE_BINDINGS.get(rule_id)


def is_production_rule(rule_id: str) -> bool:
    """判断 rule_id 是否为钦天 production 规则"""
    return rule_id in EVIDENCE_BINDINGS
