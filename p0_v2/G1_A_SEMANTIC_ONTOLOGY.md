# G1-A Semantic Ontology v1.1

> 本文件是六书切片的唯一上游契约。任何 slice 的 category/relation/node 命名必须对齐本文件。
> 冻结后通过 Ontology Guard（SHA-256 hash 锁）防止漂移。
>
> v1.1 更新：补 FOUNDATION.SHEN_SHA（神煞）；STRUCTURE 补 DUANYU/SUI_YUN；结构图同步对齐章节。

---

## 一、设计原则

1. **Node = "有什么东西"，Slice = "原文说这个东西做什么"**
   - Node 本体只定义身份：node_id / node_name / domain / sub_domain
   - subject/predicate/object 是 Slice 层字段，不是 Node 固有属性

2. **基础关系不展开成 Node**
   - 不建 `TG_JIA_SHU_MU`、`TG_JIA_SHENG_HUO` 这种节点
   - 这些通过 Slice + Relation 自然长出：`TG_JIA --BELONGS_TO--> WX_MU`

3. **经典语义 ≠ 当前命局裁决**
   - 切片只记录原文说什么，不写死"比劫克财=药"
   - 病/药是 Candidate，最终裁决由 Resolver 做

4. **SFTK 特有术语不全局冻结**
   - 雕/枯/旺/弱先作为 SFTK-specific candidate，跨书验证后再提升

---

## 二、六层 DOMAIN 结构

```
G1 Semantic Ontology v1.1
│
├── 01 FOUNDATION（基础层）
│   ├── WUXING（五行）
│   ├── YIN_YANG（阴阳）
│   ├── TIAN_GAN（天干）
│   ├── DI_ZHI（地支）
│   ├── SHI_SHEN（十神）
│   ├── YUE_LING（月令）
│   ├── DAY_MASTER（日主锚点）
│   ├── LIU_QIN（六亲）
│   └── SHEN_SHA（神煞）  ★v1.1新增
│
├── 02 STATE（状态层）
│   ├── WANG_SHUAI（旺衰）
│   ├── DE_LING（得令/失令）
│   ├── DE_DI（得地/失地）
│   ├── DE_SHI（得势/失势）
│   ├── GAN_ZHI_STATE（干支状态）
│   └── XING_QING（性情）
│
├── 03 RELATION（关系层）
│   ├── BASIC_RELATION（基础关系）
│   └── DERIVED_RELATION（派生关系）
│
├── 04 STRUCTURE（结构层）
│   ├── GE_JU（格局：含正格/变格）
│   ├── QI_SHI（气势）
│   ├── TIAO_HOU（调候）
│   ├── HUI_HE（会合）
│   ├── DUANYU（赋论断语）  ★v1.1新增
│   └── SUI_YUN（岁运）     ★v1.1新增
│
├── 05 PATHOLOGY（病理层）
│   ├── DISEASE_DOMAIN（病域分类）
│   ├── DISEASE_MECHANISM（病机制）
│   └── DISEASE_CANDIDATE（病候选，非冻结）
│
└── 06 MEDICINE（药层）
    ├── MEDICINE_MECHANISM（药机制）
    ├── MEDICINE_CANDIDATE（药候选）
    └── SHEN_ROLE（神角色：用/喜/忌）
```

---

## 三、FOUNDATION 节点全集

### 3.1 WUXING（五行）

| node_id | node_name |
|---|---|
| WX_MU | 木 |
| WX_HUO | 火 |
| WX_TU | 土 |
| WX_JIN | 金 |
| WX_SHUI | 水 |

### 3.2 YIN_YANG（阴阳）

| node_id | node_name |
|---|---|
| YY_YANG | 阳 |
| YY_YIN | 阴 |

### 3.3 TIAN_GAN（天干）

| node_id | node_name | 属五行 | 属阴阳 |
|---|---|---|---|
| TG_JIA | 甲 | WX_MU | YY_YANG |
| TG_YI | 乙 | WX_MU | YY_YIN |
| TG_BING | 丙 | WX_HUO | YY_YANG |
| TG_DING | 丁 | WX_HUO | YY_YIN |
| TG_WU | 戊 | WX_TU | YY_YANG |
| TG_JI | 己 | WX_TU | YY_YIN |
| TG_GENG | 庚 | WX_JIN | YY_YANG |
| TG_XIN | 辛 | WX_JIN | YY_YIN |
| TG_REN | 壬 | WX_SHUI | YY_YANG |
| TG_GUI | 癸 | WX_SHUI | YY_YIN |

> "甲属木/甲属阳"是 Slice Relation（BELONGS_TO），不是新 Node。

### 3.4 DI_ZHI（地支）

| node_id | node_name | 属五行 | 属阴阳 | 藏干 |
|---|---|---|---|---|
| DZ_ZI | 子 | WX_SHUI | YY_YANG | TG_GUI |
| DZ_CHOU | 丑 | WX_TU | YY_YIN | TG_JI, TG_XIN, TG_GUI |
| DZ_YIN | 寅 | WX_MU | YY_YANG | TG_JIA, TG_BING, TG_WU |
| DZ_MAO | 卯 | DZ_MAO | WX_MU | YY_YIN | TG_YI |
| DZ_CHEN | 辰 | WX_TU | YY_YANG | TG_WU, TG_YI, TG_GUI |
| DZ_SI | 巳 | WX_HUO | YY_YIN | TG_BING, TG_GENG, TG_WU |
| DZ_WU | 午 | WX_HUO | YY_YANG | TG_DING, TG_JI |
| DZ_WEI | 未 | WX_TU | YY_YIN | TG_JI, TG_DING, TG_YI |
| DZ_SHEN | 申 | WX_JIN | YY_YANG | TG_GENG, TG_REN, TG_WU |
| DZ_YOU | 酉 | WX_JIN | YY_YIN | TG_XIN |
| DZ_XU | 戌 | WX_TU | YY_YANG | TG_WU, TG_XIN, TG_DING |
| DZ_HAI | 亥 | WX_SHUI | YY_YIN | TG_REN, TG_JIA |

> 藏干是 Relation：`DZ_* --CANG--> TG_*`，不建独立藏干 Node。

### 3.5 SHI_SHEN（十神）

| node_id | node_name | 定义（Slice Relation） |
|---|---|---|
| SS_BI_JIAN | 比肩 | 日主同我同性 |
| SS_JIE_CAI | 劫财 | 日主同我异性 |
| SS_SHI_SHEN | 食神 | 日主所生同性 |
| SS_SHANG_GUAN | 伤官 | 日主所生异性 |
| SS_PIAN_CAI | 偏财 | 日主所克同性 |
| SS_ZHENG_CAI | 正财 | 日主所克异性 |
| SS_QI_SHA | 七杀 | 日主所克异性（克我） |
| SS_ZHENG_GUAN | 正官 | 日主所克同性（克我） |
| SS_PIAN_YIN | 偏印 | 日主所生同性（生我） |
| SS_ZHENG_YIN | 正印 | 日主所生异性（生我） |

> 十神定义是 Slice 出来的 Relation，不写死在 Node 里。

### 3.6 YUE_LING（月令）

不建新地支本体，12月支直接引用 DZ_*：

| 月支 | node_id |
|---|---|
| 寅月 | DZ_YIN（正月） |
| 卯月 | DZ_MAO（二月） |
| ... | ... |
| 丑月 | DZ_CHOU（十二月） |

### 3.7 DAY_MASTER（日主锚点）

```
DAY_MASTER
  ├── 日干：TG_*（随命局变化）
  ├── 日支：DZ_*（随命局变化）
  └── 日主五行：WX_*（由日干推出）
```

> 这是 RELATION 的锚点。十神关系全部以日主为基准。

### 3.8 LIU_QIN（六亲）

| node_id | node_name | 说明 |
|---|---|---|
| LQ_FU | 父 | 偏财类 |
| LQ_MU | 母 | 正印类 |
| LQ_BROTHER | 兄弟 | 比劫类 |
| LQ_QIE | 妻/夫 | 财/官杀类 |
| LQ_ZI | 子女 | 官杀/食伤类 |
| LQ_NV_MING | 女命 | 女命专论 |
| LQ_XIAO_ER | 小儿 | 小儿关煞 |

> 六亲本质是十神在人伦上的映射（正印=母、偏财=父等），但其论断对象是具体人伦关系，不等同于 SHI_SHEN 定义。

### 3.9 SHEN_SHA（神煞）

> 神煞是独立于五行生克体系之外的另一套符号系统。原文大量以"贵人入命""驿马逢冲""华盖逢空"直接论断，不归入十神/格局体系。
> 初版只冻结大类 node，具体神煞名称作为 Slice 文本内容自然生长，不逐个建 Node。

| node_id | node_name | 说明 |
|---|---|---|
| SHS_GUI_REN | 贵人类 | 天乙/天官/太极/三奇/月德/天德等贵人 |
| SHS_YI_MA | 驿马 | 奔波/迁徙/变动 |
| SHS_HUA_GAI | 华盖 | 孤高/艺术/宗教 |
| SHS_LU_SHEN | 禄神 | 福禄/食禄 |
| SHS_YANG_REN | 羊刃 | 刚烈/血光 |
| SHS_KONG_WANG | 空亡 | 虚诈/散失 |
| SHS_TAO_HUA | 桃花 | 风情/人缘 |
| SHS_JI_XIONG | 其他吉凶煞 | 将星/劫煞/亡神/灾煞等 |

> 神煞不做五行生克关系，只做"某神煞出现→某论断"的 Slice 语义。

---

## 四、STATE 节点全集

### 4.1 WANG_SHUAI（旺衰）

| node_id | node_name | 说明 |
|---|---|---|
| ST_WANG | 旺 | 日主/五行得时得势 |
| ST_SHUAI | 衰 | 日主/五行失时失势 |

### 4.2 DE_LING（得令/失令）

| node_id | node_name | 说明 |
|---|---|---|
| ST_DE_LING | 得令 | 月令为日主同类/生扶 |
| ST_SHI_LING | 失令 | 月令为日主克泄 |

### 4.3 DE_DI（得地/失地）

| node_id | node_name | 说明 |
|---|---|---|
| ST_DE_DI | 得地 | 地支有根（综合判断） |
| ST_SHI_DI | 失地 | 地支无根 |

> **边界**：DE_DI ≠ TONG_GEN。DE_DI 是综合得地状态，TONG_GEN 是具体根气关系。

### 4.4 DE_SHI（得势/失势）

| node_id | node_name | 说明 |
|---|---|---|
| ST_DE_SHI | 得势 | 天干党众 |
| ST_SHI_SHI | 失势 | 天干孤立 |

### 4.5 GAN_ZHI_STATE（干支状态）

| node_id | node_name | 说明 |
|---|---|---|
| ST_TOU_GAN | 透干 | 天干透出 |
| GEN_STATE | 根气状态 | 下分通根/无根 |
| ST_TONG_GEN | 通根 | 地支有根（GEN_STATE 下） |
| ST_WU_GEN | 无根 | 地支无根（GEN_STATE 下，通根的否定） |

### 4.6 XING_QING（性情）

| node_id | node_name | 说明 |
|---|---|---|
| ST_XING_QING | 性情 | 命主性格/禀赋，由五行十神偏枯推出 |

> 性情不是旺衰状态，是命主气质表现（相心赋/论性情等）。

---

## 五、RELATION 节点全集

### 5.1 BASIC_RELATION（基础关系）

| node_id | node_name | 方向 |
|---|---|---|
| RL_SHENG | 生 | WX/TG/DZ 直接相生 |
| RL_KE | 克 | WX/TG/DZ 直接相克 |
| RL_HE | 合 | TG 五合 / DZ 六合（原始关系） |
| RL_CHONG | 冲 | DZ 六冲 |
| RL_XING | 刑 | DZ 三刑 |
| RL_HAI | 害 | DZ 六害 |
| RL_PO | 破 | DZ 六破 |

### 5.2 DERIVED_RELATION（派生关系）

| node_id | node_name | 说明 |
|---|---|---|
| RL_XIE | 泄 | 依赖主体（我生者为泄） |
| RL_HAO | 耗 | 依赖主体（我克者为耗） |
| RL_ZHI | 制 | 依赖主体（制杀/制劫） |
| RL_HUA | 化 | 合化（需条件，≠合） |

> **HUA 归 DERIVED**：合化需要化神当令、无克破，不是直接关系。

---

## 六、STRUCTURE 节点全集

| node_id | node_name | 说明 |
|---|---|---|
| GE_JU | 格局 | 格局名（正官格/偏财格等） |
| GE_JU_ZHENG | 正格 | 八格：正官/偏官/正财/偏财/正印/偏印/食神/伤官 |
| GE_JU_BIAN | 变格 | 从格/化格/专旺等 |
| QI_SHI | 气势 | 五行聚散方向（木火通明/金水伤官等） |
| TIAO_HOU | 调候 | 寒暖燥湿调节 |
| HUI_HE | 会合 | 三会/三合局成局（结构，非原始关系） |
| DUANYU | 断语 | 总诀/赋文综合论断（无更细子域归属时） |
| SUI_YUN | 岁运 | 大运/流年/太岁对原局的作用 |

> **HE ≠ HUI_HE**：HE=原始关系（支与支发生合）；HUI_HE=结构（合而成局/三合三会）。

> **边界**：QI_SHI = 五行聚散方向；WANG_SHUAI = 五行强弱。前者看格局气势，后者看日主强弱。
>
> **DUANYU 是兜底但非垃圾桶**：只收跨格局/旺衰/喜忌的综合赋文断语；能归入 GE_JU/QI_SHI/TIAO_HOU 的仍归其类。SUI_YUN 专收大运流年对命局的作用论，不收排盘起运法（第三层）。

---

## 七、PATHOLOGY 节点全集

### 7.1 DISEASE_DOMAIN（病域分类）

| node_id | node_name | 说明 |
|---|---|---|
| STRUCTURAL_DISEASE | 结构病 | 官杀混杂/财星破印等 |
| WUXING_DISEASE | 五行病 | 五行偏枯 |
| STRENGTH_DISEASE | 强弱病 | 财多身弱/杀重身轻等 |
| PATTERN_DISEASE | 格局病 | 格局成败 |
| CLIMATE_DISEASE | 气候病 | 寒/燥/湿/热 |

### 7.2 DISEASE_CANDIDATE（工程候选分类，非经典本体冻结）

> ⚠️ candidate taxonomy only；非六部经典共同本体。原文不强行落入此分类。

| node_id | node_name | 病域 |
|---|---|---|
| BING_CAI_DUO_SHEN_RUO | 财多身弱 | STRENGTH |
| BING_SHA_ZHONG_SHEN_QING | 杀重身轻 | STRENGTH |
| BING_YIN_ZHONG_SHEN_QING | 印重身轻 | STRENGTH |
| BING_SHI_SHANG_XIE_XIU | 食伤泄秀过度 | STRENGTH |
| BING_GUAN_SHA_HUN_ZA | 官杀混杂 | STRUCTURAL |
| BING_CAI_XING_PO_YIN | 财星破印 | STRUCTURAL |
| BING_SHANG_GUAN_JIAN_GUAN | 伤官见官 | STRUCTURAL |
| BING_XIAO_SHEN_DUO_SHI | 枭神夺食 | STRUCTURAL |
| BING_BI_JIE_ZHENG_CAI | 比劫争财 | STRUCTURAL |

> **神峰四病（雕/枯/旺/弱）暂不全局冻结**，作为 SFTK-specific candidate。

---

## 八、MEDICINE 节点全集

### 8.1 MEDICINE_MECHANISM（药机制）

| node_id | node_name | 说明 |
|---|---|---|
| YAO_FU_SHEN | 扶身 | 印/比劫生扶日主 |
| YAO_ZHI_SHA | 制杀 | 食伤制杀 |
| YAO_HUA_SHA | 化杀 | 印化杀 |
| YAO_TONG_GUAN | 通关 | 中间五行调和 |
| YAO_WEN_HAN | 温寒 | 火暖寒局 |
| YAO_RUN_ZAO | 润燥 | 水润燥局 |
| YAO_QUAN_CAI | 权财 | 比劫制财（仅机制，非定论） |

> **YAO_QUAN_CAI 危险点**：不能预设"比劫克财=药"。它只是药机制候选，是否成药由 Resolver 判断。

### 8.2 SHEN_ROLE（神角色）

| node_id | node_name | 说明 |
|---|---|---|
| YONG_SHEN | 用神 | 命局最需之神 |
| XI_SHEN | 喜神 | 辅助用神 |
| JI_SHEN | 忌神 | 伤害用神 |

> 不预设具体十神归属。"X为用神"是命局裁决结果，不是 FOUNDATION Node 固有属性。

---

## 九、拓扑关系（因果链）

> ⚠️ 以下为 **ONTOLOGY INFERENCE PATH**（系统推理链），不是 canonical slice 的默认 Relation。
> 经典原文数据只允许 EXPLICIT RELATION（原文显式表达）。
> 禁止把推理边误当成原文切片关系。

| relation_type | 方向 | 说明 | 类型 |
|---|---|---|---|
| CAUSES | 原局事实 → 状态 | 导致 | INFERENCE |
| BECOMES | 状态 → 异常 | 成为 | INFERENCE |
| IS_DISEASE | 异常 → 病 | 是病 | INFERENCE |
| HAS_MECHANISM | 病 → 病机制 | 病机 | INFERENCE |
| REQUIRES | 病 → 药机制 | 需要 | INFERENCE |
| CANDIDATE_IS | 药机制 → 药候选 | 候选 | INFERENCE |
| RESOLVES_TO | 药候选 → 用神 | 归结为 | INFERENCE |
| SUPPORTS | 用神 → 喜神 | 辅助 | INFERENCE |
| CONFLICTS | 忌神 → 用神 | 冲突 | INFERENCE |
| JUDGES | 用神/忌神 → 吉凶 | 判定 | INFERENCE |
| BELONGS_TO | 节点 → 所属 | 归属 | EXPLICIT |
| GENERATES | 节点 → 所生 | 生成 | EXPLICIT |

---

## 十、Node Contract（节点契约）

每个 Node 必须满足：

```yaml
node_id: <唯一ID，大写下划线>
node_name: <中文名>
domain: <01-06 六层之一>
sub_domain: <子域>
```

**禁止：**
- ❌ Node 里写死 subject/predicate/object（那是 Slice 层）
- ❌ 为"甲属木/甲生火"建独立 Node
- ❌ 把 SFTK 特有术语直接提升全局
- ❌ 预设"比劫=药"这种结论

---

## 十一、当前冻结状态

- [x] G1-A.1 FOUNDATION（含 WUXING/YIN_YANG/TIAN_GAN/DI_ZHI/SHI_SHEN/YUE_LING/DAY_MASTER/LIU_QIN/SHEN_SHA）
- [x] G1-A.2 STATE（含 WANG_SHUAI/DE_LING/DE_DI/DE_SHI/GAN_ZHI_STATE/XING_QING）
- [x] G1-A.3 RELATION（BASIC + DERIVED）
- [x] G1-A.4 STRUCTURE（含 GE_JU/QI_SHI/TIAO_HOU/HUI_HE/DUANYU/SUI_YUN）
- [x] G1-A.5 PATHOLOGY
- [x] G1-A.6 MEDICINE
- [x] G1-A.7 TOPOLOGY
- [x] G1-A.8 Node Contract

**v1.1 变更记录：**
1. FOUNDATION 新增 SHEN_SHA（神煞）子域，解决原文神煞类内容无合法 category 的问题
2. STRUCTURE 新增 DUANYU（赋论断语），承载原文 40%+ 的赋文/口诀/总诀类主体内容
3. STRUCTURE 新增 SUI_YUN（岁运），承载大运/流年/太岁类内容
4. 结构图与章节内容对齐（此前结构图漏列 LIU_QIN/XING_QING/DUANYU/SUI_YUN）
5. GE_JU_ZHENG / GE_JU_BIAN 明确为 GE_JU 下的分类，不独立成 domain

**下一步：**
1. 生成本文件 SHA-256 hash 锁
2. 六书 × Node 检索矩阵
3. 按 v1.1 ontology 重新校验切片 category 合法性
