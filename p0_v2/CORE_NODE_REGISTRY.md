# G1 Semantic Ontology 冻结版（v1.1）

## 核心原则

```text
Node = "有什么东西"（本体）
Slice = "原文说这个东西做什么/是什么关系"（三元组）

Node本体不强制subject/predicate/object。
三元组是Slice层的字段，不是Node本体的属性。
```

---

## 一、六层DOMAIN结构

```text
G1 Semantic Ontology
│
├── 01 FOUNDATION（基础层）
│   ├── WUXING（五行）
│   ├── YIN_YANG（阴阳）
│   ├── TIAN_GAN（天干）
│   ├── DI_ZHI（地支）
│   ├── CANG_GAN（藏干）
│   ├── SHI_SHEN（十神）
│   └── YUE_LING（月令）
│
├── 02 STATE（状态层）
│   ├── WANG_SHUAI（旺衰）
│   ├── DE_LING（得令/得时）
│   ├── DE_DI（得地）
│   ├── DE_SHI（得势）
│   ├── TOU_GAN（透干）
│   └── TONG_GEN（通根）
│
├── 03 RELATION（关系层）
│   ├── BASIC_RELATION（基础关系）
│   └── DERIVED_RELATION（派生关系）
│
├── 04 STRUCTURE（结构层）
│   ├── GE_JU（格局）
│   ├── QI_SHI（气势）
│   ├── TIAO_HOU（调候）
│   ├── XING_CHONG_HE_HAI（刑冲合害）
│   └── HUI_HE（会合）
│
├── 05 PATHOLOGY（病理层）
│   ├── DISEASE_DOMAIN（病域）
│   ├── DISEASE_MECHANISM（病机）
│   └── DISEASE_CANDIDATE（病候选）
│
└── 06 MEDICINE（药层）
    ├── MEDICINE_MECHANISM（药机制）
    ├── MEDICINE_CANDIDATE（药候选）
    ├── YONG_SHEN（用神）
    ├── XI_SHEN（喜神）
    └── JI_SHEN（忌神）
```

---

## 二、FOUNDATION域（基础层）

### 2.1 WUXING（五行）

| node_id | node_name |
|---------|-----------|
| WX_MU | 木 |
| WX_HUO | 火 |
| WX_TU | 土 |
| WX_JIN | 金 |
| WX_SHUI | 水 |

### 2.2 YIN_YANG（阴阳）

| node_id | node_name |
|---------|-----------|
| YY_YANG | 阳 |
| YY_YIN | 阴 |

### 2.3 TIAN_GAN（天干）

| node_id | node_name |
|---------|-----------|
| TG_JIA | 甲 |
| TG_YI | 乙 |
| TG_BING | 丙 |
| TG_DING | 丁 |
| TG_WU | 戊 |
| TG_JI | 己 |
| TG_GENG | 庚 |
| TG_XIN | 辛 |
| TG_REN | 壬 |
| TG_GUI | 癸 |

> 注：TG_JIA保持原子节点。"甲属木/甲属阳/甲生火/甲克土"全部通过Slice三元组表达，不建新节点。

### 2.4 DI_ZHI（地支）

| node_id | node_name |
|---------|-----------|
| DZ_ZI | 子 |
| DZ_CHOU | 丑 |
| DZ_YIN | 寅 |
| DZ_MAO | 卯 |
| DZ_CHEN | 辰 |
| DZ_SI | 巳 |
| DZ_WU | 午 |
| DZ_WEI | 未 |
| DZ_SHEN | 申 |
| DZ_YOU | 酉 |
| DZ_XU | 戌 |
| DZ_HAI | 亥 |

### 2.5 CANG_GAN（藏干）

> 藏干通过Slice表达，不单独建Node。
> 例：寅中藏甲丙戊 → Slice: DZ_YIN --CANG_GAN--> TG_JIA/TG_BING/TG_WU

### 2.6 SHI_SHEN（十神）

| node_id | node_name |
|---------|-----------|
| SS_BI_JIAN | 比肩 |
| SS_JIE_CAI | 劫财 |
| SS_SHI_SHEN | 食神 |
| SS_SHANG_GUAN | 伤官 |
| SS_PIAN_CAI | 偏财 |
| SS_ZHENG_CAI | 正财 |
| SS_QI_SHA | 七杀 |
| SS_ZHENG_GUAN | 正官 |
| SS_PIAN_YIN | 偏印 |
| SS_ZHENG_YIN | 正印 |

### 2.7 YUE_LING（月令）

| node_id | node_name | 说明 |
|---------|-----------|------|
| YUE_LING | 月令 | 父节点 |
| YUE_ZI | 子月 | 引用DZ_ZI |
| YUE_CHOU | 丑月 | 引用DZ_CHOU |
| YUE_YIN | 寅月 | 引用DZ_YIN |
| YUE_MAO | 卯月 | 引用DZ_MAO |
| YUE_CHEN | 辰月 | 引用DZ_CHEN |
| YUE_SI | 巳月 | 引用DZ_SI |
| YUE_WU | 午月 | 引用DZ_WU |
| YUE_WEI | 未月 | 引用DZ_WEI |
| YUE_SHEN | 申月 | 引用DZ_SHEN |
| YUE_YOU | 酉月 | 引用DZ_YOU |
| YUE_XU | 戌月 | 引用DZ_XU |
| YUE_HAI | 亥月 | 引用DZ_HAI |

> 注：十二月令引用地支本体，不复制成另一套地支。

---

## 三、STATE域（状态层）

| node_id | node_name | 说明 |
|---------|-----------|------|
| ST_WANG | 旺 | |
| ST_SHUAI | 衰 | |
| ST_DE_LING | 得令 | 原文：得时/得令/秉令 |
| ST_SHI_LING | 失令 | 原文：失时/失令/退气 |
| ST_DE_DI | 得地 | 综合得地状态（≠通根） |
| ST_SHI_DI | 失地 | 综合失地状态 |
| ST_DE_SHI | 得势 | 原文：党众/众/强众 |
| ST_SHI_SHI | 失势 | 原文：寡/强寡/孤立 |
| ST_TOU_GAN | 透干 | |
| ST_TONG_GEN | 通根 | 根气关系（≠得地） |
| ST_WU_GEN | 无根 | |

> 关键区分：
> - TONG_GEN = 根气关系（天干在地支有根）
> - DE_DI = 综合得地状态（含通根+其他因素）
> - 两者存在条件关系，但不是等价关系

---

## 四、RELATION域（关系层）

### 4.1 BASIC_RELATION（基础关系）

| node_id | node_name | 说明 |
|---------|-----------|------|
| RL_SHENG | 生 | 五行基础生 |
| RL_KE | 克 | 五行基础克 |
| RL_TG_HE | 天干五合 | |
| RL_DZ_HE | 地支六合 | |
| RL_SANHE | 三合 | |
| RL_SANHUI | 三会 | |
| RL_CHONG | 六冲 | |
| RL_XING | 三刑 | |
| RL_HAI | 六害 | |
| RL_PO | 六破 | |

### 4.2 DERIVED_RELATION（派生关系）

| node_id | node_name | 说明 |
|---------|-----------|------|
| RL_XIE | 泄 | 依赖主体（我生者为泄） |
| RL_HAO | 耗 | 依赖主体（我克者为耗） |
| RL_ZHI | 制 | 依赖主体（制杀/制劫） |
| RL_HUA | 化 | 合化（≠合，谨慎使用） |

> 关键区分：
> - BASIC = 客观关系（木生火，不管谁是主体）
> - DERIVED = 视角关系（从日主视角看，我生为泄，我克为耗）

---

## 五、STRUCTURE域（结构层）

| node_id | node_name | 说明 |
|---------|-----------|------|
| GE_JU | 格局 | 父节点 |
| GE_JU_ZHENG | 正格 | 八格 |
| GE_JU_BIAN | 变格 | 特殊格 |
| QI_SHI | 气势 | 关键中间层，不可缺 |
| TIAO_HOU | 调候 | |
| XING_CHONG_HE_HAI | 刑冲合害 | |
| HUI_HE | 会合 | |

---

## 六、PATHOLOGY域（病理层）

### 6.1 DISEASE_DOMAIN（病域分类）

| node_id | 说明 |
|---------|------|
| STRUCTURAL_DISEASE | 结构病 |
| WUXING_DISEASE | 五行病 |
| STRENGTH_DISEASE | 强弱病 |
| PATTERN_DISEASE | 格局病 |
| CLIMATE_DISEASE | 调候病 |

### 6.2 DISEASE_CANDIDATE（病候选集，第一批）

#### STRENGTH_DISEASE（强弱病候选）

| node_id | node_name |
|---------|-----------|
| BING_CAI_DUO_SHEN_RUO | 财多身弱 |
| BING_SHA_ZHONG_SHEN_QING | 杀重身轻 |
| BING_YIN_ZHONG_SHEN_QING | 印重身轻 |
| BING_SHI_SHANG_XIE_XIU | 食伤泄秀过度 |
| BING_GUAN_SHA_HUN_ZA | 官杀混杂 |
| BING_CAI_XING_PO_YIN | 财星破印 |
| BING_SHANG_GUAN_JIAN_GUAN | 伤官见官 |
| BING_XIAO_SHEN_DUO_SHI | 枭神夺食 |
| BING_BI_JIE_ZHENG_CAI | 比劫争财 |

#### CLIMATE_DISEASE（调候病候选）

| node_id | node_name |
|---------|-----------|
| BING_HAN | 寒 |
| BING_ZAO | 燥 |
| BING_SHI | 湿 |
| BING_RE | 热 |

> 注：
> - 以上是Disease Candidate，不是最终Disease Graph
> - DiseaseNode结构：disease_id / name / cause / affected_object / mechanism / conditions / exclusion_conditions / related_nodes / source_evidence
> - 神峰四病（雕/枯/旺/弱）暂作为SFTK特有候选，不全局冻结

---

## 七、MEDICINE域（药层）

### 7.1 MEDICINE_MECHANISM（药机制）

| node_id | node_name | 说明 |
|---------|-----------|------|
| YAO_FU_SHEN | 扶身 | 机制（印/比劫为候选） |
| YAO_ZHI_SHA | 制杀 | 机制（食伤/印为候选） |
| YAO_HUA_SHA | 化杀 | 机制（印为候选） |
| YAO_TONG_GUAN | 通关 | 机制（中间五行为候选） |
| YAO_WEN_HAN | 温寒 | 机制（火为候选） |
| YAO_RUN_ZAO | 润燥 | 机制（水为候选） |
| YAO_QU_GUAN_LIU_SHA | 去官留杀 | 机制 |
| YAO_QU_SHA_LIU_GUAN | 去杀留官 | 机制 |

### 7.2 MEDICINE_CANDIDATE（药候选）

> 具体药（印/比劫/某干/某支/某运）由Resolver根据条件判断，不预设。

### 7.3 用神/喜神/忌神

| node_id | node_name | 说明 |
|---------|-----------|------|
| YONG_SHEN | 用神 | 保留节点，不预设具体归属 |
| XI_SHEN | 喜神 | 保留节点，不预设具体归属 |
| JI_SHEN | 忌神 | 保留节点，不预设具体归属 |

> 关键防火墙：
> - 原典语义 ≠ 当前命局裁决
> - 比劫克财 ≠ 药（由Resolver判断）
> - 食伤泄秀 ≠ 财多身弱的药（由Resolver判断）

---

## 八、拓扑关系（因果链）

```text
RELATION_TYPE
├── CAUSES（导致）        原局事实 → 状态
├── BECOMES（成为）       状态 → 异常/矛盾
├── IS_DISEASE（是病）    异常/矛盾 → 病候选
├── HAS_MECHANISM（病机） 病 → 病机制
├── REQUIRES（需要）      病 → 药机制候选
├── CANDIDATE_IS（候选）  药机制 → 药候选
├── RESOLVER_JUDGE（Resolver裁决）  药候选 → 用神
├── SUPPORTS（辅助）      用神 → 喜神
├── CONFLICTS（冲突）     忌神 → 用神
└── JUDGES（判定）        用神/忌神 → 吉凶
```

> 关键：RESOLVER_JUDGE是防火墙
> - 原典语义层只记录"病需要什么机制"
> - 具体哪个五行/干支是药，由Resolver根据命局条件判断
> - 不能在Ontology层预设"X就是Y的药"

---

## 九、Node本体 vs Slice三元组

```text
Node本体（只记"是什么"）:
  node_id: TG_JIA
  node_name: 甲
  domain: FOUNDATION
  sub_domain: TIAN_GAN

Slice三元组（记"原文说什么"）:
  subject: TG_JIA
  predicate: BELONGS_TO
  object: WX_MU
  evidence: "甲属木"

  subject: TG_JIA
  predicate: BELONGS_TO
  object: YY_YANG
  evidence: "甲属阳"

  subject: TG_JIA
  predicate: GENERATES
  object: TG_BING
  evidence: "甲生丙"
```

---

## 十、裁决记录

```text
裁决#001: TG_JIA不展开子节点，保持原子性
裁决#002: 病/药分层（STRENGTH/CLIMATE/SFTK_SPECIFIC）
裁决#003: FOUNDATION加YUE_LING
裁决#004: STATE区分得地/通根
裁决#005: RELATION分Basic/Derived两层
裁决#006: STRUCTURE补QI_SHI
裁决#007: PATHOLOGY分Disease Domain/Mechanism/Candidate
裁决#008: MEDICINE分Mechanism/Candidate
裁决#009: 神峰四病暂不全局冻结
裁决#010: subject/predicate/object从Node模板移到Slice层
```

---

## 十一、对齐原则

```text
1. Node = 有什么东西（本体）
2. Slice = 原文说什么（三元组）
3. 原典语义 ≠ 当前命局裁决
4. 病候选 ≠ 最终病Graph
5. 药机制 ≠ 具体药
6. 没有原文支撑的节点 = 理论推导 = 禁止
```
