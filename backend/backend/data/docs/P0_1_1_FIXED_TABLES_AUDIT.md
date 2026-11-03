# P0-1.1 Source Reconciliation Report — 固定数据表全量审计

> **审计时间**：2026-08-29
> **审计范围**：所有固定数据表（十二长生、藏干、合冲刑害、空亡、五合、三会等）
> **审计原则**：只审计，不重构
> **基于 commit**：`eca458d`
> **前置报告**：`docs/P0_1_SOURCE_DIFF_REPORT.md`（十二长生、藏干、十神）

---

## 审计总结

| 类别 | 已找到表数 | 重复实现 | 数据错误 | 缺失表 |
|------|-----------|----------|----------|--------|
| 基础事实 | 3 | 2 | 1（十二长生丁己） | 0 |
| 地支关系 | 6 | 4 | 0 | 1（三会） |
| 天干关系 | 1 | 0 | 0 | 2（天干冲、天干克） |
| 其他 | 2 | 0 | 0 | 若干 |

**总计**：12 张已找到的固定数据表，6 张重复实现，1 张有数据错误，至少 3 张缺失。

---

## 一、已找到的固定数据表清单

### 1.1 基础事实表

| 表名 | 位置 | 状态 | 备注 |
|------|------|------|------|
| 十二长生表 | `bazi_l1_facts.py::TIAN_GAN_TWELVE_GROWTH` | ❌ **丁己错误** | 阴干顺布而非逆布，20个错误 |
| 十二长生表 | `bazi_fixed_tables.py::LONGHU_STAGE` | ✅ 正确 | 阳顺阴逆，火土同生 |
| 藏干表 | `bazi_l1_facts.py::BRANCH_HIDDEN_STEMS` | ✅ 数据正确 | 字典结构，中文key |
| 藏干表 | `bazi_ten_gods.py::BRANCH_HIDDEN_STEMS` | ✅ 数据正确 | 列表结构，英文tuple |
| 天干五行映射 | `bazi_engine.py::STEM_ELEMENT` | ✅ 正确 | 英文key |
| 天干五行映射 | `bazi_l1_facts.py::TIAN_GAN_WU_XING` | ✅ 正确 | 中文key |

### 1.2 地支关系表

| 表名 | 位置 | 状态 | 重复实现 |
|------|------|------|----------|
| 六冲表 | `bazi_engine.py::BRANCH_CLASH` | ✅ 正确 | `blind_bazi_engine.py::BRANCH_CHONG` |
| 六害表 | `bazi_engine.py::BRANCH_HARM` | ✅ 正确 | `blind_bazi_engine.py::BRANCH_CHUAN` |
| 六合表 | `bazi_engine.py::BRANCH_HE` | ✅ 正确 | `blind_bazi_engine.py::BRANCH_LIUHE` |
| 三合表 | `bazi_engine.py::BRANCH_SANHE` | ✅ 正确 | `blind_bazi_engine.py::BRANCH_SANHE` |
| 三刑表 | `bazi_engine.py::BRANCH_SANXING` | ✅ 正确 | 无 |
| 空亡表 | `bazi_engine.py::KONG_WANG_BY_XUN` | ✅ 正确 | 无 |

### 1.3 天干关系表

| 表名 | 位置 | 状态 | 备注 |
|------|------|------|------|
| 天干五合表 | `blind_bazi_engine.py::STEM_HE` | ✅ 正确 | **只有一套**，在盲派引擎中 |

### 1.4 其他表

| 表名 | 位置 | 状态 | 备注 |
|------|------|------|------|
| 墓库表 | `blind_bazi_engine.py::MU_KU` | ✅ 正确 | 辰水墓、戌火墓、丑金墓、未木墓 |
| 桃花表 | `bazi_engine.py::PEACH_BLOSSOM_BY_DAY` | ✅ 正确 | 以日支查桃花 |

---

## 二、重复实现分析

### 2.1 六冲表（2套实现）

**bazi_engine.py::BRANCH_CLASH**（第44-51行）：
```python
BRANCH_CLASH = {
    "ZI": "WU", "WU": "ZI",
    "CHOU": "WEI", "WEI": "CHOU",
    ...
}
```

**blind_bazi_engine.py::BRANCH_CHONG**（第48-55行）：
```python
BRANCH_CHONG = {
    'ZI': 'WU', 'WU': 'ZI',
    'CHOU': 'WEI', 'WEI': 'CHOU',
    ...
}
```

**对比结果**：✅ 数据完全一致，只是变量名不同（CLASH vs CHONG）。

### 2.2 六害表（2套实现）

**bazi_engine.py::BRANCH_HARM** vs **blind_bazi_engine.py::BRANCH_CHUAN**

**对比结果**：✅ 数据完全一致。盲派叫"穿"，子平叫"害"，是同一概念。

### 2.3 六合表（2套实现，结构不同）

**bazi_engine.py::BRANCH_HE**（第80-87行）：
```python
BRANCH_HE = {
    frozenset({"ZI", "CHOU"}): "EARTH",
    frozenset({"YIN", "HAI"}): "WOOD",
    ...
}
```
结构：frozenset key → 化气五行

**blind_bazi_engine.py::BRANCH_LIUHE**（第30-37行）：
```python
BRANCH_LIUHE = {
    'ZI': 'CHOU', 'CHOU': 'ZI',
    'YIN': 'HAI', 'HAI': 'YIN',
    ...
}
```
结构：字典 key → value（双向映射），**没有化气五行**

**对比结果**：
- ✅ 六合配对关系一致
- ⚠️ 结构不同：bazi_engine 有化气五行，blind_bazi_engine 没有
- ⚠️ blind_bazi_engine 的六合表缺少化气五行信息

### 2.4 三合表（2套实现，结构不同）

**bazi_engine.py::BRANCH_SANHE**（第91-96行）：
```python
BRANCH_SANHE = {
    frozenset({"SHEN", "ZI", "CHEN"}): "WATER",
    ...
}
```
结构：frozenset key → 合化五行

**blind_bazi_engine.py::BRANCH_SANHE**（第40-45行）：
```python
BRANCH_SANHE = {
    'SHEN-ZI-CHEN': {'SHEN', 'ZI', 'CHEN'},  # 水局
    'HAI-MAO-WEI': {'HAI', 'MAO', 'WEI'},    # 木局
    ...
}
```
结构：字符串key → set value，**合化五行只在注释中**

**对比结果**：
- ✅ 三合配对关系一致
- ⚠️ 结构不同
- ⚠️ blind_bazi_engine 的注释提到"原SHEN-MAO-WEI错误"，说明之前有过错误，已修复

### 2.5 十神计算（2套实现）

**bazi_engine.py::_ten_god()** vs **bazi_ten_gods.py::ten_god()**

**对比结果**：✅ 100/100 完全一致（见 P0-1 报告）

---

## 三、缺失的固定数据表

### 3.1 地支三会表 ❌ 缺失

**标准子平三会**：
- 寅卯辰 → 木局
- 巳午未 → 火局
- 申酉戌 → 金局
- 亥子丑 → 水局

**当前状态**：在核心引擎（bazi_engine.py、bazi_l1_facts.py、bazi_fixed_tables.py）中**未找到三会表的定义**。

搜索结果显示"寅卯辰""巳午未"等出现在 `judgment_engine.py`、`daily_state_service.py` 等文件中，但可能是在文本中提到，而不是作为固定数据表定义。

**影响**：三会局是地支关系的重要组成部分，缺失会导致 Canonical State 不完整。

### 3.2 天干相冲表 ❌ 缺失

**标准天干相冲**：
- 甲庚冲
- 乙辛冲
- 丙壬冲
- 丁癸冲
- 戊己不冲（同属土）

**当前状态**：未找到天干相冲表的定义。

### 3.3 天干相克表 ⚠️ 隐含在五行生克中

天干相克实际上是五行相克：
- 甲乙木克戊己土
- 丙丁火克庚辛金
- 戊己土克壬癸水
- 庚辛金克甲乙木
- 壬癸水克丙丁火

**当前状态**：五行生克关系可能隐含在十神计算中，但没有独立的固定数据表。

### 3.4 地支相破表 ❌ 缺失

**标准地支相破**：
- 子酉破
- 午卯破
- 巳申破
- 寅亥破
- 辰丑破
- 戌未破

**当前状态**：未找到地支相破表的定义。

---

## 四、数据正确性验证

### 4.1 六冲表 ✅ 正确

标准六冲：子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲
bazi_engine.py::BRANCH_CLASH：完全一致 ✅

### 4.2 六害表 ✅ 正确

标准六害：子未害、丑午害、寅巳害、卯辰害、申亥害、酉戌害
bazi_engine.py::BRANCH_HARM：完全一致 ✅

### 4.3 六合表 ✅ 正确

标准六合：子丑合土、寅亥合木、卯戌合火、辰酉合金、巳申合水、午未合土
bazi_engine.py::BRANCH_HE：完全一致 ✅（含化气五行）

### 4.4 三合表 ✅ 正确

标准三合：申子辰合水、亥卯未合木、寅午戌合火、巳酉丑合金
bazi_engine.py::BRANCH_SANHE：完全一致 ✅

### 4.5 三刑表 ✅ 正确

标准三刑：
- 寅巳申三刑（无恩之刑）
- 丑戌未三刑（恃势之刑）
- 子卯刑（无礼之刑）
- 辰午酉亥自刑

bazi_engine.py::BRANCH_SANXING：完全一致 ✅

### 4.6 空亡表 ✅ 正确

标准空亡（六甲旬）：
- 甲子旬空戌亥
- 甲戌旬空申酉
- 甲申旬空午未
- 甲午旬空辰巳
- 甲辰旬空寅卯
- 甲寅旬空子丑

bazi_engine.py::KONG_WANG_BY_XUN：完全一致 ✅

### 4.7 天干五合表 ✅ 正确

标准天干五合：甲己合、乙庚合、丙辛合、丁壬合、戊癸合
blind_bazi_engine.py::STEM_HE：完全一致 ✅

**但注意**：天干五合表只在盲派引擎中有，通用引擎 bazi_engine.py 中没有。

### 4.8 墓库表 ✅ 正确

标准墓库：辰=水墓、戌=火墓、丑=金墓、未=木墓
blind_bazi_engine.py::MU_KU：完全一致 ✅

### 4.9 桃花表 ✅ 正确

标准桃花（以日支查）：
- 寅午戌 → 卯
- 巳酉丑 → 午
- 申子辰 → 酉
- 亥卯未 → 子

bazi_engine.py::PEACH_BLOSSOM_BY_DAY：完全一致 ✅

---

## 五、重要发现

### 5.1 发现 1：十二长生表有 20 个数据错误 🔴

详见 P0-1 报告。`bazi_l1_facts.py` 的丁和己两个阴干十二长生表错误（阴干顺布而非逆布），`bazi_fixed_tables.py` 正确。

### 5.2 发现 2：地支三会表缺失 🔴

三会局是地支关系的重要组成部分，但在核心引擎中未找到定义。

### 5.3 发现 3：天干五合表只有一套，且在盲派引擎中 ⚠️

天干五合表 `STEM_HE` 只在 `blind_bazi_engine.py` 中定义，通用引擎 `bazi_engine.py` 中没有。这意味着通用引擎可能无法计算天干五合关系。

### 5.4 发现 4：合冲刑害表存在重复实现 ⚠️

六冲、六害、六合、三合表在 `bazi_engine.py` 和 `blind_bazi_engine.py` 中各有一套实现，数据基本一致但结构不同。后续应统一为一套。

### 5.5 发现 5：空亡注释包含隐性评分 ⚠️

`calc_kong_wang` 的注释写着"空亡之字力量减半"，这是隐性评分！虽然代码本身没有实现"力量减半"，但注释暗示了这种处理方式。按 P0 执行约束，空亡应该是 Relation Effect Modifier，不是 Strength Evidence，不能"力量减半"。

### 5.6 发现 6：blind_bazi_engine.py 的三合表曾有错误 ⚠️

`blind_bazi_engine.py::BRANCH_SANHE` 的注释提到"原SHEN-MAO-WEI错误"，说明之前三合表有过错误（亥卯未写成了申卯未），已修复。这证明固定数据表确实可能有错误，必须审计。

---

## 六、固定数据表统一建议（仅建议，不执行）

### 6.1 应统一到 Canonical Source Registry 的表

| 表名 | 建议来源 | 原因 |
|------|----------|------|
| 十二长生表 | `bazi_fixed_tables.py::LONGHU_STAGE` | 正确，阳顺阴逆 |
| 藏干表 | 数据一致，统一结构即可 | 两套数据一致 |
| 天干五行映射 | 任一，统一结构即可 | 两套数据一致 |
| 六冲表 | `bazi_engine.py::BRANCH_CLASH` | 正确，通用引擎 |
| 六害表 | `bazi_engine.py::BRANCH_HARM` | 正确，通用引擎 |
| 六合表 | `bazi_engine.py::BRANCH_HE` | 正确，含化气五行 |
| 三合表 | `bazi_engine.py::BRANCH_SANHE` | 正确，含合化五行 |
| 三刑表 | `bazi_engine.py::BRANCH_SANXING` | 正确 |
| 空亡表 | `bazi_engine.py::KONG_WANG_BY_XUN` | 正确 |
| 天干五合表 | `blind_bazi_engine.py::STEM_HE` | 需迁移到通用引擎 |
| 墓库表 | `blind_bazi_engine.py::MU_KU` | 需迁移到通用引擎 |
| 桃花表 | `bazi_engine.py::PEACH_BLOSSOM_BY_DAY` | 正确 |

### 6.2 需补充的表

- 地支三会表
- 天干相冲表
- 地支相破表
- 五行生克表（独立定义）

### 6.3 需移除的隐性评分

- `calc_kong_wang` 注释中的"空亡之字力量减半"

---

## 七、下一步

### P0-1.2 原典认证（工程一致后）
- [ ] 十二长生体系（阳顺阴逆、火土同生）的原典依据
- [ ] 藏干分层（本气/中气/余气）的原典依据
- [ ] 合冲刑害空亡的原典依据
- [ ] 天干五合的原典依据

### P0-2 全仓隐性评分扫描
- [ ] 完成 blind_bazi_engine.py 详细扫描
- [ ] 完成 judgment_engine.py 详细扫描
- [ ] 完成 annual_event_evaluator.py 详细扫描
- [ ] 扫描 reasoning/ 目录
- [ ] 扫描 signal/ 目录
- [ ] 记录空亡"力量减半"等隐性评分注释

### P0-3 Canonical State 最小闭环
- **禁止提前**：必须等 P0-1 和 P0-2 完成后才能开始

---

## 八、审计脚本

本次审计使用的脚本：`scripts/p0_1_source_reconciliation.py`（十二长生、藏干、十神对比）

固定数据表全量审计为人工核对 + 代码审查，暂未自动化。

---

*本报告是 P0-1.1 Source Reconciliation 的成果，覆盖所有已找到的固定数据表。后续将补充原典认证和缺失表的补充。*
