# 六部经典切片单元规范（冻结版）

## 总则

### 核心铁律
1. 切片 = 一个原典语义事实，不是关键词命中
2. 每个切片必须回答：讲什么对象、什么关系、什么条件、什么结果
3. Relation只提取原文显式表达，禁止理论推导、禁止共现误判
4. 原文没有 → null / ZERO_HIT，禁止用命理知识补
5. 不替用户裁决争议，保留分歧原文

### 统一切片单元字段
```json
{
  "slice_id": "STRING",           // 唯一ID
  "book": "STRING",               // DTS_LB / PZZQ / QTBJ / YHZP / SFTK / SMTH
  "section": "STRING",             // 篇/区
  "chapter": "STRING",            // 章
  "category": "STRING",           // 20类一级分类
  "subject": "STRING",            // 切片主体（这段原文在讲谁）
  "source_text": "STRING",        // 原文（不改）
  "source_location": {            // 可回溯
    "file": "STRING",
    "chapter": "STRING",
    "paragraph": "INT",
    "hash": "STRING"
  },
  "conditions": ["STRING"],       // 原文明确给出的条件
  "result": "STRING",             // 原文明确给出的结果
  "relations": [                  // 只提取显式表达
    {
      "source": "STRING",
      "relation": "STRING",
      "target": "STRING",
      "evidence": "STRING"        // 原文哪句话支撑
    }
  ],
  "status": "ACCEPT"              // ACCEPT / FLAG / ZERO_HIT
}
```

### 禁止字段
```
❌ our_interpretation     （SFTK争议切片禁止加解释）
❌ system_supplied_data   （系统补的假数据）
❌ inferred_condition     （系统推的条件）
❌ inferred_result        （系统推的结果）
```

---

## 第一本：《滴天髓》DTS_LB

### 基本信息
- 文件: DTS_滴天髓_京图撰刘基原注.md
- 结构: 上篇34章 + 下篇29章 = 63章
- 注意: 绝对不能混任铁樵《滴天髓阐微》

### 切片单元规范

| 项目 | 规范 |
|------|------|
| 允许搜索区域 | 全书按### 章节切 |
| 切片触发条件 | 每章一个完整语义单元，按### 标题切 |
| 切片最小完整单元 | 一章 = 一个切片 |
| 必须保留字段 | slice_id, book, section, chapter, category, subject, source_text, conditions, result, relations |
| 禁止推导字段 | conditions/result只能从原文提取，禁止用命理知识补 |
| ZERO_HIT条件 | 该章节无明确语义事实（纯过渡/纯引言） |

### 章节主体锁定（防P22错误）
```
P22错误: 丙火章里出现"甲木"就被判成甲木切片

正确做法:
  天干章: 主体是天干本身，不是文中提到的每个天干
  - "甲木参天..." → 主体=甲木
  - "丙火猛烈..." → 主体=丙火
  - 丙火章里提到"甲木" → 主体还是丙火，不是甲木

锁定规则:
  切片主体 = 章节标题规定的主体
  不是文中出现的任何干支
```

### 重点章节
```
天干章 → 10个天干各一个切片（甲~癸）
地支章 → 按地支性质切
衰旺章 → 主体=旺衰判定方法
病药相关章 → 病和药分开切
从象/化象/假从/假化 → 主体=该格局判定条件
```

### 分类映射
```
天道/地道/人道/知命 → FOUNDATION
理气/衰旺/中和/精神/性情 → WANG_SHUAI
配合/干支总论/合局 → GANZHI
天干/地支 → FOUNDATION
形象/方局/八格/官杀/伤官/从象/化象/假从/假化/顺局/反局/战局/君象/臣象/母象/子象/震兑/坎离 → GE_JU
体用/源流/通关/闲神 → YONG_SHEN
月令/生时 → YUE_LING
清气/浊气/真神/假神/刚柔/顺逆/隐显/众寡/才德/奋郁/恩怨 → QI_SHI
寒暖/燥湿 → TIAO_HOU
战局 → XING_CHONG
夫妻/子女/父母/兄弟/何知章/女命章/小儿/疾病/出身/地位 → JI_XIONG
岁运/贞元 → LIU_NIAN
```

---

## 第二本：《子平真诠》PZZQ

### 基本信息
- 文件: PZZQ_子平真诠.txt
- 特点: 月令→格局→用神→成败完整体系

### 切片单元规范

| 项目 | 规范 |
|------|------|
| 允许搜索区域 | 全书按章切 |
| 切片触发条件 | 每个格局判定条件 = 一个语义单元 |
| 切片最小完整单元 | 一章 = 一个切片；同章内不同格局 = 多个切片 |
| 必须保留字段 | slice_id, book, chapter, category, pattern_name, success_conditions, fail_conditions, use_direction, source_text |
| 禁止推导字段 | success_conditions/fail_conditions只能从原文提取，原文没讲 = null |
| ZERO_HIT条件 | 原文没讲该格的成/败/顺/逆 → 该字段=null，不是ZERO_HIT |

### 格局切片（检索覆盖，不是强制填充）
```
八格检索覆盖:
  正官/七杀/正财/偏财/正印/偏印/食神/伤官/建禄/月刃

每格检索:
  格成条件 → 原文有就提取，没有=null
  格破条件 → 原文有就提取，没有=null
  顺用/逆用 → 原文有就提取，没有=null
  相神有无 → 原文有就提取，没有=null
  救应条件 → 原文有就提取，没有=null

禁止:
  ❌ 原文没讲就用命理知识补"财官印食顺用"
  ❌ 原文没讲就用命理知识补"杀伤劫刃逆用"
```

### 大运切片
```
必须保留:
  原局条件 + 运的变化 + 为什么发生变化

禁止:
  ❌ 只切"某大运吉"这种笼统判断
```

---

## 第三本：《穷通宝鉴》QTBJ

### 基本信息
- 文件: QTBJ_穷通宝鉴.txt
- 特点: 月令×日主×调候×配合，最特殊

### 切片单元规范

| 项目 | 规范 |
|------|------|
| 允许搜索区域 | 全书按"天干×月令"专题切 |
| 切片触发条件 | 找到该专题原文连续语义单元 |
| 切片最小完整单元 | 一个天干×月令 = 一个专题切片 |
| 必须保留字段 | slice_id, book, day_master, month, climate, primary_need, secondary_need, combination, outcome, source_text |
| 禁止推导字段 | primary_need/secondary_need只能从原文提取，原文没讲 = null |
| ZERO_HIT条件 | 整个专题无原文证据 = ZERO_HIT（不是强行填120个） |

### 120专题检索覆盖（不是强制填充）
```
10天干 × 12月令 = 120专题

每个专题:
  找到原文连续语义单元 → 提取字段
  找不到 → ZERO_HIT

禁止:
  ❌ 为了凑满120个而填primary_need
  ❌ 系统认为"甲木寅月应该用丙火"就填丙火
  ❌ 用命理知识补"春木必须用火"

正确:
  原文写了"先取丙火" → primary_need=丙火
  原文没写 → primary_need=null
  整个专题原文都没有 → status=ZERO_HIT
```

### 调候专用字段
```
climate: 原文明确说的寒暖燥湿
primary_need: 原文说的"先取"
secondary_need: 原文说的"次取"
combination: 原文说的配合条件
outcome: 原文说的成败结果

全部只从原文提取，不补。
```

---

## 第四本：《渊海子平》YHZP

### 基本信息
- 文件: YHZP_渊海子平.md
- 特点: 基础体系+完整子平框架，切得最全面

### 切片单元规范

| 项目 | 规范 |
|------|------|
| 允许搜索区域 | 全书按章切 |
| 切片触发条件 | 每个十神/每个格局 = 一个语义单元 |
| 切片最小完整单元 | 一章 = 一个切片；同章内不同十神 = 多个切片 |
| 必须保留字段 | slice_id, book, chapter, category, shishen, definition, conditions, auspicious, inauspicious, source_text |
| 禁止推导字段 | definition/auspicious/inauspicious只能从原文提取，原文没讲 = null |
| ZERO_HIT条件 | 原文没讲该十神的definition/喜/忌 → 该字段=null |

### 十神检索覆盖（不是强制填充）
```
十神检索覆盖:
  比肩/劫财/食神/伤官/偏财/正财/七杀/正官/偏印/正印

每个十神检索:
  十神是什么 → 原文有就提取，没有=null
  十神得令 → 原文有就提取，没有=null
  十神透干 → 原文有就提取，没有=null
  十神坐支 → 原文有就提取，没有=null
  十神生克 → 原文有就提取，没有=null
  十神成格 → 原文有就提取，没有=null
  十神为喜 → 原文有就提取，没有=null
  十神为忌 → 原文有就提取，没有=null

禁止:
  ❌ 原文没讲就用命理知识补"正官克我者异性"
  ❌ 原文没讲就用命理知识补"正官为喜"
```

### 神煞
```
第一轮不切，放OTHER/SECONDARY。
不要让神煞把主线切片工程带偏。
```

---

## 第五本：《神峰通考》SFTK

### 基本信息
- 文件: SFTK_神峰通考.txt
- 特点: 格局争议+取用争议+具体命例验证

### 切片单元规范

| 项目 | 规范 |
|------|------|
| 允许搜索区域 | 全书按章切 |
| 切片触发条件 | 每个争议点/每个病药说 = 一个语义单元 |
| 切片最小完整单元 | 一章 = 一个切片；同章内不同争议 = 多个切片 |
| 必须保留字段 | slice_id, book, chapter, category, debate, bing, yao, source_text |
| 禁止推导字段 | debate只能记录原文观点，禁止加our_interpretation |
| ZERO_HIT条件 | 无争议点 = 普通切片，不是ZERO_HIT |

### 争议切片（禁止裁决）
```
看到"辨/论/或曰/又曰/此说/非/不然/误/正/偏"

切片格式:
{
  "category": "GE_JU",
  "debate": {
    "viewpoint_A": "原文观点A",
    "viewpoint_B": "原文观点B",
    "condition_diff": "原文说的条件差异"
  },
  "source_text": "原文完整段落"
}

禁止:
  ❌ our_interpretation字段
  ❌ "我认为观点A对"
  ❌ "应该按观点B"
  ❌ 任何替用户裁决的内容
```

### 病药切片
```
一段同时说"某结构为病，须以某五行制之":
  BING: 某结构（原文明确说的病）
  YAO: 某五行（原文明确说的药）
  BING_YAO: 病→药关系

病和药分开切，不合并。
```

---

## 第六本：《三命通会》SMTH

### 基本信息
- 文件: SMTH_三命通会.txt
- 特点: 内容庞杂，必须分区切

### 切片单元规范

| 项目 | 规范 |
|------|------|
| 允许搜索区域 | 六大区域 |
| 切片触发条件 | 每个明确关系语句 = 一个关系切片 |
| 切片最小完整单元 | 一个完整语义单元 |
| 必须保留字段 | slice_id, book, section, chapter, category, source, relation, target, condition, source_text |
| 禁止推导字段 | 关系必须从原文明确提取，禁止共现误判 |
| ZERO_HIT条件 | 无明确关系语句 = 不生成关系切片 |

### 六区搜索范围（不是六种固定模板）
```
第一区: 基础理论
  FOUNDATION / SHENG_KE

第二区: 格局十神
  YUE_LING / GE_JU / SHISHEN / WANG_SHUAI / QI_SHI

第三区: 刑冲合害（重点）
  TG_HE / DZ_HE / SANHE / SANHUI / CHONG / XING / HAI / PO

第四区: 病药用神
  BING / YAO / YONG_SHEN / XI_SHEN / JI_SHEN

第五区: 大运流年
  DA_YUN / LIU_NIAN
  必须保留: 原局 → 运 → 变化 → 结果

第六区: 命例
  ZAO_XIANG
  命例必须保留完整上下文，不拆成一句一句
```

### 关系切片铁律
```
必须能回答: 谁 与谁 发生 什么关系

✅ 提取:
  "甲己合" → TG_HE(甲,己)
  "子丑合" → DZ_HE(子,丑)
  "亥卯未木局" → SANHE(亥,卯,未)
  "子午冲" → CHONG(子,午)

❌ 不提取:
  "带合" → 不知道谁与谁合
  "逢合" → 不知道谁与谁合
  文中出现"合"字 → 不知道是什么合
```

---

## 六本书重点分工

| 书 | 第一重点 | 第二重点 | 第三重点 |
|----|----------|----------|----------|
| DTS_LB | 病药 | 生克制化 | 旺衰/用神 |
| PZZQ | 月令→格局 | 用神成败 | 岁运 |
| QTBJ | 调候 | 月令条件 | 用神配合 |
| YHZP | 完整子平体系 | 十神 | 格局/岁运 |
| SFTK | 格局取用辨析 | 病药 | 命例验证 |
| SMTH | 综合体系 | 干支刑冲合害 | 岁运/命例 |

---

## 验收标准（六书通用）

```
✅ 原文可回溯（source_location完整）
✅ 切片不改原文（source_text = 原文原文）
✅ 主体明确（subject = 章节标题规定的主体）
✅ 条件明确（conditions = 原文明确给出）
✅ 语义明确（result = 原文明确给出）
✅ Relation有显式原文依据（evidence = 原文哪句话）
✅ 无共现推导（文中出现X和Y但没说关系 = 不生成Relation）
✅ 无理论补全（原文没讲 = null，不用命理知识补）
✅ 无跨书污染（六经典独立，不互相调用）
✅ 没有显式关系就绝对不生成Relation
```
