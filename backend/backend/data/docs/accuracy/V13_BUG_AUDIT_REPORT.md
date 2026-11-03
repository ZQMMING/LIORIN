# 顺天项目全面 BUG 审查报告

**审查日期**: 2026-08-22
**审查者**: Claude (via Hermes delegation)
**项目路径**: D:/today/backend
**状态**: 已归档，待修复

---

## 一、BUG 清单（按优先级排序）

### P0 — 阻塞产品化的关键缺陷

#### BUG-P0-01: Yi Engine 解释层是占位输出
- **文件**: `src/tongshu/engines/yi/relational_interpretation.py:65-77`
- **问题**: 函数返回硬编码字符串，注释明确写 "返回占位输出，完整实现需要接入 LLM"
- **输出内容**:
  - `state`: 仅拼接卦名+体用关系，无实质分析
  - `opportunity`: "需结合具体人生领域分析"（万能废话）
  - `attention`: "参考爻辞与经典注解"（推诿）
  - `suggestion`: "咨询专业易学顾问"（推诿）
  - `confidence`: 硬编码 0.7（虚假置信度）
- **影响**: Yi Engine 解释层完全无效，用户看到的是无意义的模板文字
- **修复建议**: 接入 LLM（受约束的 prompt），或至少使用 `yi/interpreter.py` 中已有的规则引擎逻辑
- **预估工作量**: 2-3天（接入 LLM）或 1天（复用 yi/interpreter.py 逻辑）

#### BUG-P0-02: 经典原文库为空字典
- **文件**: `src/tongshu/engines/yi/classical_text.py:13,28-42`
- **问题**: `CLASSICAL_TEXTS: dict[str, dict] = {}` 是空字典，`get_classical_text()` 返回全空字符串
- **注释**: "简化版经典原文数据库...完整实现应加载 D:\wiki\Obsidian\Hermes\tongshu\易经经典原文库\"
- **影响**: 层 C（经典层）完全无数据，导致下游 ImageExpansion 和 Interpretation 都缺少经典依据
- **修复建议**: 实现 `load_classical_database()` 从知识库加载，或从 KbLoader 的 passages 中提取易经相关原文
- **预估工作量**: 3-5天（需整理64卦卦辞/彖辞/大象辞数据）

#### BUG-P0-03: 河洛+易经未接入主 Pipeline
- **文件**: `src/tongshu/pipeline_stages/compute_stage.py`
- **问题**: ComputeStage 只调用 bazi + ziwei + huangli 三引擎，**完全没有调用 HeluoCanonical 或 YiInterpreter**
- **证据**: grep 搜索 `heluo|HeluoCanonical|YiInterpreter` 在 compute_stage.py 中零结果
- **影响**: 河洛引擎和易经解释引擎在生产流程中完全不运行，是"幽灵模块"
- **修复建议**: 在 ComputeStage 中增加 HeluoCanonical 调用阶段，并将结果传入 YiAdapter → YiInterpretationEngine
- **预估工作量**: 2-3天

#### BUG-P0-04: 三套解释引擎并存，职责混乱
- **发现三套独立的解释实现**:
  1. `engines/yi/relational_interpretation.py` — 占位符（P0-01）
  2. `engines/heluo/interpretation.py` — H4 引擎，有完整逻辑（因子权重/五行修正/时间衰减），但**未被任何 pipeline 调用**
  3. `yi/interpreter.py` — Phase 6 引擎，有规则逻辑（体用关系→方向标签），但**未被 pipeline 调用**
- **影响**: 代码冗余，维护成本高，产品化时不知道用哪个
- **修复建议**: 统一为一套解释引擎，建议以 `yi/interpreter.py` 为基础（它符合 Schema 9 契约）
- **预估工作量**: 3-5天（合并+测试）

---

### P1 — 影响数据质量的关键缺陷

#### BUG-P1-01: 卦序数据有重复/缺失
- **文件**: `src/tongshu/engines/yi/hexagram_symbol.py:34-48`
- **问题**:
  - GUA_SEQUENCE 中 "讼" 出现两次（位置3和16），"履" 出现两次（位置4和20）
  - 实际只有约42个唯一卦名，缺少22卦
  - `HEXAGRAM_FULL_DATA` 字典为空（循环体是 `pass`）
  - `hexagram_number` 始终返回 0
- **影响**: 卦序查找不可靠，部分卦名无法正确解析
- **修复建议**: 修正 GUA_SEQUENCE 为标准64卦序，填充 HEXAGRAM_FULL_DATA
- **预估工作量**: 1-2天

#### BUG-P1-02: 互卦计算未实现
- **文件**: `src/tongshu/engines/yi/hexagram_symbol.py:154-157`
- **问题**: 函数体只有 `return ""`，注释 "简化实现"
- **影响**: 互卦数据缺失，YiStructure.auxiliary_relations 不完整
- **修复建议**: 实现互卦算法（取2-3-4爻为下卦，3-4-5爻为上卦）
- **预估工作量**: 0.5天

#### BUG-P1-03: 河洛时间序列（流年/流月/流日卦）是占位
- **文件**: `src/tongshu/engines/heluo/temporal.py:24-50`
- **问题**: `compute_timeline()` 返回空列表，注释 "当前实现为占位，具体时间卦计算待版本锁定后接入"
- **影响**: 时间引擎无法提供流年/流月/流日卦象，Yi 解释缺少时间维度
- **修复建议**: 实现基于本命卦+目标日期的时间卦计算
- **预估工作量**: 3-5天

#### BUG-P1-04: 象扩展层数据极度稀疏
- **文件**: `src/tongshu/engines/yi/image_expansion.py:11-45`
- **问题**: 只生成2个 ImageItem（1个 level_1 + 1个 level_2），level_3/4/5 全部为空
- **影响**: 象义推导链几乎为空，LLM 解释缺少素材
- **修复建议**: 从知识库的 passages/concepts 中加载卦象类象数据
- **预估工作量**: 2-3天

#### BUG-P1-05: 承乘关系字段名混淆
- **文件**: `src/tongshu/engines/yi/line_symbol.py:46-47`
- **问题**: 返回时 `cheng_cheng=relations["cheng"]` 和 `cheng=relations["cheng_cheng"]`，字段名交叉赋值
- **影响**: 承/乘关系数据错位，爻象分析结果不正确
- **修复建议**: 修正字段映射
- **预估工作量**: 0.5天

#### BUG-P1-06: 传给 LLM 的上下文数据错误
- **文件**: `src/tongshu/engines/yi/relational_interpretation.py:48-49`
- **问题**: `"cheng": input.line_symbol.cheng_cheng` 和 `"cheng_cheng": input.line_symbol.cheng`，与 P1-05 同样的交叉问题
- **影响**: 传给 LLM 的上下文数据错误
- **修复建议**: 与 P1-05 一起修正
- **预估工作量**: 含在 P1-05 中

---

### P2 — 架构一致性与测试覆盖

#### BUG-P2-01: Profile Gate 三态未实现
- **文件**: `src/tongshu/api/app.py:316`
- **问题**: 仅有注释 `"mock_until_profile_gate_or_content_module"`，无实际 ProfileGate 实现
- **影响**: 无法根据 Profile 完整度控制输出质量（INSUFFICIENT/PARTIAL/VALID）
- **修复建议**: 实现 ProfileGate 检查逻辑
- **预估工作量**: 2天

#### BUG-P2-02: CalculationContext 未被主 Pipeline 统一消费
- **文件**: `src/tongshu/pipeline_stages/compute_stage.py:68-76`
- **问题**: ComputeStage.run() 接收原始 `birth_date: tuple[int,int,int,int]`，而非 CalculationContext
- **影响**: 时间解析（真太阳时/日柱边界）在 pipeline 中未标准化
- **修复建议**: 让 ComputeStage 接收 CalculationContext，通过 bazi_view/ziwei_view 投影
- **预估工作量**: 1-2天

#### BUG-P2-03: 解释层测试只测结构不测质量
- **文件**: `tests/yi/test_yi_e2e.py`, `tests/spec/test_relational_interpretation.py`
- **问题**: 测试只验证字段存在/类型正确，不验证解释内容是否有意义
- **缺失测试**:
  - 解释内容是否引用了具体卦辞/爻辞
  - 不同卦象是否产生不同解释
  - 体用关系是否正确映射到方向标签
  - 禁止术语检查是否覆盖所有输出
- **修复建议**: 增加内容质量测试（至少10个 case）
- **预估工作量**: 2天

#### BUG-P2-04: 测试数量实际为 1264 而非 293
- **发现**: `pytest --co -q` 显示 1264 tests collected
- **影响**: 如果之前报告293是通过的测试数，说明有大量测试被 skip/xfail
- **修复建议**: 确认哪些测试被跳过，分析原因
- **预估工作量**: 0.5天（诊断）

#### BUG-P2-05: NFC API 端点大部分未实现
- **文件**: `src/tongshu/api/nfc.py:82-104`
- **问题**: `/nfc/relationship` 和 `/nfc/state` 返回 `{"status": "IMPLEMENTING"}`
- **影响**: NFC 产品化场景（双人通书/每日状态）不可用
- **修复建议**: 实现完整逻辑
- **预估工作量**: 3-5天

---

## 二、审计报告

### 2.1 五引擎集成状态

| 引擎 | 实现状态 | Pipeline 集成 | 数据输出 |
|------|---------|--------------|---------|
| 八字 (Bazi) | ✅ 完整 | ✅ ComputeStage 调用 | ✅ BaziChart |
| 紫微 (Ziwei) | ✅ 完整(含iztro) | ✅ ComputeStage 调用 | ✅ ZiweiChart |
| 黄历 (Huangli) | ✅ 完整(lunar_python) | ✅ ComputeStage 调用 | ✅ HuangliDay |
| 河洛 (Heluo) | ✅ 完整(8模块) | ❌ 仅 NFC API 调用 | ⚠️ HeluoResult 未进入 SIR |
| 易经 (Yi) | ⚠️ 三套并存 | ❌ 完全未集成 | ❌ 占位输出 |

**结论**: 五引擎中只有三引擎（八字/紫微/黄历）真正参与主流程。河洛引擎仅在 NFC 端点使用。易经引擎完全游离于系统之外。

### 2.2 数据闭环状态

```
Evidence → Rule → Engine → Interpretation 闭环分析:

✅ Evidence: KbLoader 完整，link closure 验证到位
✅ Rule: rule_db.py + rule_loader.py 正常
✅ Engine: Bazi/Ziwei/Huangli 计算正确
❌ Engine → Interpretation: 断裂！
   - HeluoCanonical 结果未传入 YiAdapter
   - YiAdapter 未被 ComputeStage 调用
   - relational_interpretation 是占位符
   - 知识库中的易经 passages 未被 classical_text.py 使用
```

**结论**: Evidence → Rule → Engine 链路闭合，但 Engine → Interpretation 链路完全断裂。知识库中的易经数据（passages/concepts）未被解释层消费。

### 2.3 测试覆盖状态

| 模块 | 测试存在 | 测试质量 | 覆盖盲区 |
|------|---------|---------|---------|
| Bazi Engine | ✅ 充分 | ✅ 确定性验证 | 无 |
| Ziwei Engine | ✅ 充分 | ✅ Golden case | 无 |
| Huangli Engine | ✅ 充分 | ✅ 双源校验 | 无 |
| Heluo Engine | ✅ 充分 | ✅ Golden case(纪晓岚) | 无 |
| Yi Engine (engines/yi) | ⚠️ 仅结构测试 | ❌ 不测内容质量 | 解释质量/LLM输出 |
| Yi Engine (yi/) | ✅ E2E测试 | ⚠️ 测方向标签 | 经典引用完整性 |
| H4 Interpretation | ✅ 单元测试 | ⚠️ 测结构不测语义 | 未被pipeline调用 |
| Pipeline 集成 | ✅ ComputeStage | ❌ 不含 Heluo/Yi | 五引擎联动 |

**结论**: 计算层测试充分，解释层测试严重不足。1264 个测试中，没有任何测试验证"解释内容是否有意义"。

### 2.4 架构一致性状态

| 架构要求 | 实现状态 | 备注 |
|---------|---------|------|
| Architecture Freeze V1.0 §2.3 河洛8模块 | ✅ 已实现 | canonical/prenatal/postnatal/yuantang/temporal/hexagram/numbers/input |
| Schema 9 (YiStructure/YiInterpretation) | ✅ 已定义 | yi/schema.py 完整 |
| G1.9 InterpInput 禁止 raw calc | ✅ 已实现 | spec/test_relational_interpretation.py 验证 |
| Profile Gate 三态 | ❌ 未实现 | 仅有注释占位 |
| CalculationContext 统一消费 | ⚠️ 部分 | NFC API 使用，主 Pipeline 未使用 |
| 禁止 fortune_score | ✅ 已实现 | YiInterpretation.has_fortune_score 恒返回 False |
| 禁止术语检查 | ✅ 已实现 | FORBIDDEN_TERMS + check_forbidden_terms() |
| Evidence Chain 闭合 | ✅ 已实现 | chain/chain_context.py + validate_chain() |

---

## 三、关键发现总结

1. **系统存在"三套 Yi 解释引擎"的架构混乱**，其中两套有实际逻辑但未被调用，一套是占位符却被定义为正式接口
2. **河洛引擎是"幽灵模块"** — 实现完整（8模块+Golden Case），但只在 NFC API 中使用，主 Pipeline 完全绕过
3. **知识库与解释层断裂** — KbLoader 有完善的易经 passages/concepts 数据，但 classical_text.py 用的是空字典
4. **测试数量充足（1264个）但质量分布不均** — 计算层测试充分，解释层只测结构不测语义
5. **A3.6-A 评分 3.3% 的根因**: 不是算法问题，而是解释层根本没接入真实数据和 LLM

---

## 四、下一步行动建议

### 必须立即修复（阻塞产品化）

1. **BUG-P0-03**: 将 HeluoCanonical + YiAdapter + YiInterpretationEngine 接入 ComputeStage
   - 这是最关键的断裂点，修复后五引擎才真正联动
   
2. **BUG-P0-01 + P0-04**: 统一解释引擎
   - 建议以 `yi/interpreter.py` 为基础（它已有规则逻辑且符合 Schema 9）
   - 废弃 `engines/yi/relational_interpretation.py` 的占位实现
   - 将 `engines/heluo/interpretation.py` 的因子权重逻辑合并到统一引擎

3. **BUG-P0-02**: 实现 classical_text.py 的知识库加载
   - 从 KbLoader 的 passages 中筛选易经相关原文
   - 至少覆盖64卦卦辞 + 大象辞

### 可以延后（不影响 MVP）

4. **BUG-P1-03**: 时间序列卦（流年/流月/流日）— 等版本锁定后实现
5. **BUG-P1-04**: ImageExpansion 扩展 — 等经典原文库就绪后填充
6. **BUG-P2-01**: Profile Gate — 等 Profile 模块稳定后实现
7. **BUG-P2-05**: NFC relationship/state 端点 — Phase 7-B/C 范围

### 修复顺序建议

```
Week 1: P0-03 (Pipeline 接入) + P0-04 (统一解释引擎)
Week 2: P0-01 (替换占位输出) + P0-02 (经典原文加载)
Week 3: P1-01 (卦序修正) + P1-02 (互卦) + P1-05 (承乘修正)
Week 4: P2-03 (解释质量测试) + P1-04 (象扩展)
```

---

**审查完成。未修改任何代码文件。所有发现均基于源码静态分析。**

**归档日期**: 2026-08-22
**归档者**: Hermes (Engineering Auditor)
