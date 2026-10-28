# PATCH-002 Concept 语义隔离方案（2026-09-16 · 修订版 v2）

> 依据：PATCH-001 §12/§13 + Human 裁决 2026-09-16（方向成立，证据须逐条重新钉死）
> **修订原因**：v1 报告直接从 OCR 文本提取关键词、未区分 text_layer 与章节语境，违反「证据链只准古书原文逐字」铁律。Human 指出后全量重查。
> 关键升级：**Concept 隔离必须到「章节/Rule 语境」层，不能只到「书籍」层**——滴天髓反局篇内部「印旺」尚分君赖臣生/儿能生母/母慈灭子三种子语境。

---

## 一、同词异义审计（修订版 · 证据逐条钉死）

### 1.1 「印旺」六部证据钉死表（text_layer + 章节 + 可靠等级）

| 引擎 | 章节 | source_id | text_layer | 原文铁证 | 语义 | 状态 |
|---|---|---|---|---|---|---|
| DTS | 六親論·反局 | DTS-045-001 | **ORIGINAL A** | 「君賴臣生理最微，兒能生母洩天機。母慈滅子關頭異」 | 反局总纲（印旺致害） | ✅ 可靠 |
| DTS | 六親論·反局·注 | DTS-045-002 | **ANNOTATION B** | 「木旺謂之慈母，反使火熾而焚滅子」+ 君赖臣/儿能生母细分 | 印旺反局三子语境 | ✅ 可靠（注） |
| DTS | 六親論·何知章·注 | DTS-033-014 | **ANNOTATION B** | 「身弱印輕…元神厚處」（任氏注） | 印轻而有辅=元神厚 | ✅ 可靠（注） |
| DTS | 六親論·何知章 | DTS-033-015 | **UNVERIFIED D** | 「印綬太旺，日主無着落…皆壽歿之人」 | 印太旺→夭 | ⚠️ 待核（非正文对句非注，来源未验） |
| PZZQ | 論用神格局高低 | PZZQ-007-001 | **ORIGINAL A** | 「身強印旺透煞，孤貧…身旺不勞印生」 | 身强印旺反忌 | ✅ 可靠 |
| PZZQ | 論用神格局高低 | PZZQ-007-022 | **ORIGINAL A** | 「身弱逢之，最喜印旺」 | 身弱喜印旺 | ✅ 可靠 |
| QTBJ | 二月丁火 | QTBJ-040-001 | **ORIGINAL A** | 「得印旺殺高大富大貴」 | 调候贵征（特定月干） | ✅ 可靠 |
| QTBJ | 五月戊土 | QTBJ-049-001 | **ORIGINAL A** | 「兩透印旺殺高出將入相」 | 调候贵征（特定月干） | ✅ 可靠 |
| YHZP | 子機賦 | YHZP-138-001 | **ORIGINAL A** | 「身旺印多，喜行財地」 | 身旺印多喜财 | ✅ 可靠 |
| YHZP | 寸金搜髓論 | YHZP-131-001 | **ORIGINAL A** | 「身旺印旺，破財不聚」 | 身旺印旺破财 | ✅ 可靠 |
| SMTH | 卷八·六丁日壬寅時斷 | SMTH-092-007 | **ORIGINAL A** | 「寅午年月身旺，申子辰官旺，亥卯未印旺，俱可言貴」 | 丁巳日壬寅时·年月支三合语境 | ✅ 可靠（网络多源验证） |
| SFTK | 印綬格·補曰 | SFTK-022-010 | **ANNOTATION B**（修正） | 「補曰…印旺遇財乃發」（张楠补注） | 印旺为病财为药 | ⚠️ 注解层，不作 A 级 |
| SFTK | （《崖泉男命赋》引文） | — | **LATER_COMMENTARY** | 「印旺一見財鄉，自然家肥屋潤」 | 印旺见财发（赋文） | ⚠️ 引文归属，不入 Rule |

### 1.2 关键证据修正（v1 错误逐条纠正）

1. **DTS「身弱印輕」**：v1 当 A 级原文 → 实为**何知章·任氏注（ANNOTATION B）**。证据链：注层可作 B 级，**不得作 A 级 Golden**。
2. **DTS「印綬太旺日主無着落」**：v1 当原文 → 实为 DTS-033-015 **UNVERIFIED D**（未验证层）。**待核后才能入证据链**——不能因为「印旺」出现就当原文。
3. **SMTH「亥卯未印旺俱可言貴」**：v1 引错 source_id（072-009）→ 真实出处 **SMTH-092-007（六丁日壬寅時斷·丁巳日壬寅时）**，网络多源（古文岛/汉典古籍/抖音百科）验证一致。语境=**具体日时断语**（丁巳日壬寅时的年月支三合结构），不是泛论。
4. **SFTK「印旺遇財乃發」**：v1 当 A 级原文 → 实为 **SFTK-022-010 補曰（张楠补注，注解层）**；网络查证「印旺一見財鄉」出自**《崖泉男命赋》**（神峰通考引文）。**均不作 A 级**。
5. **SFTK 系统性 text_layer 错误**：176 条「補曰/註/釋」开头条目错标 ORIGINAL/A → **已全量修正为 ANNOTATION/B**（2026-09-16 执行）；91 条「歌/詩」开头登记待批（未机械改）。

### 1.3 滴天髓反局内部细分（Human 裁决核心证据）

DTS-045-002 任氏注（ANNOTATION B）明示三种「印旺」反局子语境：

| 子概念 | 注文 | 判定 |
|---|---|---|
| 君賴臣生 | 「木浮水泛，土止水則生木…皆君賴臣也」 | 印旺需他行制化救 |
| 兒能生母 | 「木被金傷，火尅金則生木…皆兒能生母」 | 食伤救印 |
| 母慈滅子 | 「木旺謂之慈母，反使火熾而焚滅子」 | 印旺过甚反害（**印旺致害**） |

**结论**：同一「印旺」（DTS 反局篇），内部三种子语境——概念隔离必须下沉到 **章节·Rule 语境** 层。

## 二、Concept 隔离机制（修订版：下沉到章节语境）

### 2.1 concept_id 命名升级

```
v1（书籍层）：CONCEPT-<BOOK>-<CONCEPT>
        ↓
v2（章节·Rule 语境层）：CONCEPT-<BOOK>-<CHAPTER>-<CONCEPT>[-<SUBCONCEPT>]
```

示例：
- `CONCEPT-DTS-FANJU-YINWANG-MUCI_MIEZI`（母慈灭子）
- `CONCEPT-DTS-FANJU-YINWANG-JUNLAI_CHENSHENG`（君赖臣生）
- `CONCEPT-DTS-HEZHIZHANG-YINQING`（何知章·印轻·任注）
- `CONCEPT-PZZQ-YONGSHEN-GEJU-YINWANG`（真诠·论用神格局高低·印旺）

### 2.2 concept_registry.json schema（v2）

```json
{
  "concept_id": "CONCEPT-DTS-FANJU-YINWANG-MUCI_MIEZI",
  "book": "滴天髓",
  "engine": "DI_TIAN_SUI",
  "chapter": "六親論·反局",
  "concept": "印旺·母慈滅子",
  "text_layer": "ORIGINAL",
  "evidence_grade": "A",
  "semantic_domain": "反局·印旺致害",
  "state_domain": "CONDITION_STATE",
  "source_ids": ["DTS-045-001", "DTS-045-002"],
  "rule_ids": [],
  "text_evidence": "「母慈滅子關頭異」「木旺謂之慈母，反使火熾而焚滅子」",
  "version": "1.0.0",
  "status": "PENDING"
}
```

字段铁律：
- `text_layer` / `evidence_grade`：**必须与 source 一致**（注层=ANNOTATION/B，正文=ORIGINAL/A，未验证=D）
- `chapter`：必填（章节语境隔离）
- `source_ids`：证据链逐条绑定
- 注层证据的 concept 必须显式标 `text_layer=ANNOTATION`，**不得伪装 ORIGINAL**

### 2.3 引擎执行约束（v2）

1. 派生概念规则必须带 `concept_id`（含章节层级），未注解 → FAIL_CLOSED
2. **同书同词不同章节 = 不同 concept**（如 DTS 反局印旺 ≠ 何知章印轻）
3. 证据等级 A/B/D 分别入 Golden 的等级权重，**D 级（UNVERIFIED）不得入规则**

## 三、SFTK 91 条「歌/詩」text_layer 定性（P0 完成，2026-09-16）

### 3.1 定性结果

| 类别 | 数量 | text_layer | evidence_grade | 依据 |
|---|---|---|---|---|
| 歌釋/詩釋 开头 | 81 | **ANNOTATION** | **B** | 「釋」=对歌诀/断语的解释（《继善篇》体例：正文→歌釋逐句解，诗词汇/QQ阅读原文证实） |
| 歌曰/詩曰 开头 | 9 | **QUOTED_SOURCE**（新登记） | **D** | 歌诀引用（前贤赋文或张楠自作，出处待核）；含「碧淵賦云」引用的明确标注 |
| 空「詩釋」 | 1（SFTK-125-038） | ANNOTATION | B | 内容缺失，status=NEEDS_REVIEW |
| **合计** | **91** | — | — | 全部不再作 ORIGINAL/A |

### 3.2 QUOTED_SOURCE 新层登记（V2.22 附录 D 扩展）

V2.22 附录 D 原 5 值（ORIGINAL/ANNOTATION/LATER_COMMENTARY/UNVERIFIED/NEEDS_REVIEW）无引用层。Human 2026-09-16 点名 QUOTED_SOURCE，登记为工程扩展层：

```
QUOTED_SOURCE：正文引用的他典/歌诀原文（如《碧渊賦》《崖泉男命賦》引文、前贤歌诀）。
- 文本本身可靠可作证据，但归属=原出处，不冒充本书 ORIGINAL
- 原出处已确认 → evidence_grade 最高 A（绑定原典 source）
- 原出处待核 → evidence_grade = D（UNVERIFIED），不入规则
- 禁止以 QUOTED_SOURCE 冒充 ORIGINAL/A 的本书证据
```

### 3.3 混合条目（违反 D-4 Mixed Source，登记待拆）

OCR 转录切分未按「正文/注解/引用」分层，以下条目正文+注解/引用混排，**须拆条**（source_id 重分配 + rules 引用核查，待 Human 批准）：

| source_id | 章节 | 混排内容 |
|---|---|---|
| SFTK-018-012 | 古時純偏官有制例 | 古歌云×3 + 補曰 |
| SFTK-043-003 | 歲德扶殺格 | 正文 + 補曰 + 淵海註曰 + 纂要歌曰 + 古歌曰 |
| SFTK-062-038 | 十天干體象全編論 | 申宮詩曰 + 酉宮詩曰…（多宫诗引用） |
| SFTK-124-025 | 總言篇 | 正文歌诀 + 歌釋 |
| SFTK-124-064 | 總言篇 | 正文断语 + 歌釋 |
| SFTK-124-095 | 總言篇 | 正文断语 + 歇釋 |
| SFTK-124-107 | 總言篇 | 正文断语 + 歌釋 + 歌釋 |
| SFTK-125-029 | 六神篇 | 詩釋 + 断语 + 詩釋 + 断语 + 詩釋…（8 处嵌套） |
| SFTK-125-057 | 六神篇 | 正文断语 + 詩釋 |

## 四、D-4 Mixed Source 清零（P0 完成，2026-09-16）

### 4.1 拆条结果：9 条混排 → 67 个语义单元

| 原 source_id | 章节 | 拆成单元 | 单元构成 |
|---|---|---|---|
| SFTK-018-012 | 古時純偏官有制例 | 8 | 古歌云×3 + 補曰 + 又歌曰×2 + 解曰×2 |
| SFTK-043-003 | 歲德扶殺格 | 12 | 正文断语×3 + 補曰×2 + 淵海註曰×2 + 纂要歌曰 + 古歌曰 + 纂要云 + 歌曰 |
| SFTK-062-038 | 十天干體象全編論 | 6 | 申/酉/戌/亥宮詩曰×4 + 總咏 + 干支所屬残片 |
| SFTK-124-025 | 總言篇 | 6 | 正文歌诀 + 歌釋×5 |
| SFTK-124-064 | 總言篇 | 2 | 正文断语 + 歌釋 |
| SFTK-124-095 | 總言篇 | 2 | 正文断语 + 歇釋 |
| SFTK-124-107 | 總言篇 | 13 | 正文断语×6 + 歌釋×5 + 命例 + 页标 |
| SFTK-125-029 | 六神篇 | 16 | 正文断语×7 + 詩釋×8 + 页标 |
| SFTK-125-057 | 六神篇 | 2 | 正文断语 + 詩釋 |

**source_id 规则**：原 ID 作废，子单元 = `SFTK-<章>-<条>-NN`（如 SFTK-125-029-02）。每个单元独立 text_layer / evidence_grade，RuleEngine 引用必须精确到子单元。
**页标**（「神峰通考 卷五 一五」等转录页码）：独立记录，text_layer=UNVERIFIED，notes 标注「转录页码标记，非古籍正文」。

### 4.2 拆条后 text_layer 分布（SFTK 全库 2519 条）

ORIGINAL 2208 / ANNOTATION 283 / QUOTED_SOURCE 25 / UNVERIFIED 3。

## 五、QUOTED_SOURCE 重定义（Human 裁决 2026-09-16）

```
QUOTED_SOURCE
  ↓ 表示「当前书籍正在引用其他文本」
  ↓ 不是当前书籍作者正文
  ↓ 必须继续追溯 origin_source

SFTK
 └─ QUOTED_SOURCE
      ├─ quoted_origin       = 《碧渊赋》《淵海子平》註等
      ├─ origin_source_id    = 原典绑定（待核 None）
      └─ origin_verification = PENDING / VERIFIED
```

铁律：**《神峰通考》引用《碧渊赋》，不能把《碧渊赋》的话升级成《神峰通考》原创文**。只有追到真正出处后，原典文本才可作对应经典 A 级证据。

## 六、歌釋/詩釋 定性（SFTK 文献体例解释层）

非「现代意义上的注解」——是 SFTK 文献体例中的解释层。工程上归 ANNOTATION，但保留细粒度身份，**不得粗暴合并所有 ANNOTATION 为同一作者**：

```
ANNOTATION
  annotation_type = SONG_EXPLANATION | SUPPLEMENT | EXPLANATION | NOTE
  attribution     = SFTK_TRADITION（歌釋/詩釋·体例解释层）
                  | ZHANG_NAN（補曰/又補·张楠）
                  | UNKNOWN（解曰·待考）
```

本次拆条已全部落 annotation_type + attribution（67 单元全含）。

## 七、CLASSICAL_RULE_ADMISSION 硬门槛（Human 拍板，永久锁死）

业务规则进入裁决阶段必须全部满足：

```
① 指定六部经典
② 精确篇章
③ 原文逐字
④ text_layer = ORIGINAL
⑤ evidence_grade = A
⑥ 章节语境完整
⑦ 条件完整
⑧ 不得跨书籍偷换语义
⑨ 不得把注解升级原文
⑩ 不得把引用文升级本书原文
⑪ Rule → Evidence → Test → Golden → Admission
```

任何一项失败 → **FAIL_CLOSED**（不得模型自行补全）。
数据治理通过 ≠ 经典裁决结论。测试通过只证明工程未破坏，不等于规则获得裁决资格。

## 八、8 条印系 Rule → **HOLD（Human 裁决）**

继续暂停。拆条后 9 条印系证据（DTS-045-001/002、PZZQ-007-001/022、QTBJ-040-001/049-001、YHZP-131-001/138-001、SMTH-092-007）已全部钉死为 ORIGINAL/A 或 ANNOTATION/B，但**未完成语义拆分与 Rule Admission**，不得提前。

## 九、待办（下一批）

- [x] D-4 混排拆条（9 条 → 67 单元，已清零）
- [ ] 歌曰/詩曰 等 QUOTED_SOURCE 原出处核验（origin_verification PENDING → VERIFIED，绑定原典）
- [ ] DTS-033-015「印綬太旺日主無着落」版本核验（UNVERIFIED → 定层）
- [ ] **六部经典原文逐条复核**（拆条后全量：text_layer/章节/原文逐字）→ 完成后才裁决身旺/身弱、财、官、清、浊
- [ ] concept_registry.json 创建（v2 schema）待 Human 批准

## 十、本次执行记录（2026-09-16）

1. SFTK 176 条注解错标 → ANNOTATION/B ✅
2. SFTK 91 条歌/詩 定性（81 ANN + 9 QUOTED + 1 NEEDS_REVIEW）✅
3. D-4 混排 9 条 → 67 单元拆条（ORIGINAL/ANNOTATION/QUOTED_SOURCE/UNVERIFIED 各归其位）✅
4. QUOTED_SOURCE 重定义（quoted_origin/origin_source_id/origin_verification）✅
5. 歌釋/詩釋 annotation_type + attribution 落库 ✅
6. CLASSICAL_RULE_ADMISSION 十一道门槛落档 ✅
7. SMTH-092-007 网络多源验证 ✅
8. 测试 257 passed ✅
