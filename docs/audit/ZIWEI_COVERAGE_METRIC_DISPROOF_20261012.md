# 千文千问线勘查：引擎同一性 + 命中率口径证伪

**日期**：2026-10-12
**触发**：核实 `D:\Documents\qwen-agent\RuR7DQQMG1\default\` 是否为同一紫微引擎 + 复核「命中率 1.9%」口径
**方法**：只读勘查 + 实跑复现，不修改该目录任何内容

---

## 一、引擎同一性：确认**同一个**

`ziwei_calibrate_v4.py:7-9` 直接 import 顺天引擎：

```python
sys.path.insert(0, r"D:\shuntian\src")
from lunar_python import Solar
from tongshu.engines.ziwei_engine import ZiweiEngine, GAN_SIHUA
```

`proofread_dims.py:5-11` 同样：

```python
sys.path.insert(0, r"D:\shuntian\src")
from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.interpretation import build_life_reading
from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals
from tongshu.engines.ziwei.rules import answer_layer as AL

ze = ZiweiEngine(node_modules_dir=Path(r"D:\shuntian\node_modules"))
```

**结论**：`D:\Documents\qwen-agent\RuR7DQQMG1\default\` 是**千文千问线的工作目录**，
`D:\shuntian` 是其**引擎依赖**（同源、同 Golden 集、同 node_modules）。
不存在"两套引擎"——所有脚本都是 `sys.path` 指向顺天 `src`。

### 1.1 该目录内容性质

| 类别 | 文件 | 说明 |
|------|------|------|
| 校准/校对 | `ziwei_calibrate_v4.py`、`proofread_dims.py`、`proofread_article.py` | 对文章断语做验真 |
| 案例运行 | `run_ziwei_cases_desktop.py`、`run_cases_post_z52.py`、`case_1983_11_3.py` | 桌面 13 例 / 窗口 3 例 |
| 分阶段验证 | `verify_z50_effect.py`、`verify_z51.py`、`verify_z52.py`、`verify_z53_full.py` | Z50~Z53 逐阶段 |
| 快照 | `baseline_nonziwei.txt`、`after_input_guard.txt`、`after_bazi_connect.txt`、`ab_head_version.txt` | 变更前后对比 |
| 提交物 | `commit_msg_z53.txt` | 与 `02b5ecc0` 提交信息一致 |
| 步进脚本 | `step1_rebalance_qtn.py`、`step23_mount_and_expand.py`、`step25_fidelity_fix.py` | Z50/Z51 施工 |

> `commit_msg_z53.txt` 内容与 `D:\shuntian` 的 `02b5ecc0` 提交信息**逐字一致**，
> 印证该目录是本轮 Z50~Z53 工作的原始现场。

---

## 二、命中率口径证伪：1.9% 是**度量方法的伪低值**

### 2.1 口径定义（`proofread_dims.py:66-71`）

```python
full_blob = " ".join([ans_blob, nihai_blob] + list(dim_conc.values()))

def chk(domain, key, claim_list):
    for c in claim_list:
        hit = c in full_blob      # ← 精确子串匹配
```

即：把文章里**人工撰写的长句断语**，拿去和引擎输出整段文本做**逐字子串匹配**。

### 2.2 实测复跑结果

```
A 六大领域: 4/83 命中 (4.8%)
B 十二宫逐宫: 5/76 命中 (6.6%)
总: 9/159 命中 (5.7%)
```

（本次复跑得 5.7%；交接方报 1.9%，量级一致、均为同法伪低值。）

### 2.3 证伪证据：引擎实际**已逐字输出**被判 ✗ 的内容

**样例一 —— 疾厄宫**

| | 文本 |
|---|---|
| 文章（判 ✗） | `生年科自带修复力小病容易痊愈遇良医` |
| 引擎实际输出 | `疾厄自化科，**生年科自带修复力，小病容易痊愈遇良医**。` |

引擎**逐字包含**该句，仅因前缀「疾厄自化科，」+ 断句逗号，导致 `in` 匹配失败。

**样例二 —— 疾厄宫陀罗**

| | 文本 |
|---|---|
| 文章（判 ✗） | `陀罗代表慢性病反复缠绵` |
| 引擎实际输出 | `陀罗入疾厄，慢性病反复缠绵，难以根治` |

语义完全对应，字符串不同 → 判 ✗。

**样例三 —— 福德宫**

| | 文本 |
|---|---|
| 文章（判 ✗） | `紫微守福德内心自尊心极强`（等 5 条全 ✗） |
| 引擎实际输出 | `精神世界丰富，有追求和理想。` |

此例属**真实覆盖差异**：文章该段有实质人工综合，引擎侧仅给出概括句。
即：伪低值中**混有真实缺口**，需分离。

### 2.4 结论

「1.9%（或 5.7%）命中率」**不能作为引擎覆盖能力的指标**，原因：

1. **度量目标错位**：度量的是「文章句子能否被逐字检索到」，而非「引擎覆盖了多少语义单元」。
2. **分母不可比**：文章断语为人工综合写作（含大量润色、串联、语气词），
   任何规则引擎都不可能原样输出；分母天然偏向"不可命中"。
3. **混入真实缺口**：确有一部分（如福德宫）引擎覆盖不足，被伪低值掩盖，
   需按语义单元重新归因。

---

## 三、建议的正确口径

替换 `in` 精确匹配为**语义单元级**评测：

| 维度 | 建议做法 |
|------|---------|
| 匹配粒度 | 拆为「星曜 × 宫位 × 吉凶/事件」三元组，而非整句 |
| 匹配方式 | 关键词集合覆盖（如陀罗+慢性病 → 命中），或规则化归一后比对 |
| 分母定义 | 限定为**引擎规则库可表达的语义单元**，剔除纯人工综合句 |
| 分档输出 | 明确区分 `命中` / `语义等价但措辞不同` / `真实缺口` |
| 样本固化 | 落为 `scripts/ziwei_coverage_audit.py`，可复跑、可 diff |

**关键**：应把"真实缺口"（如福德宫覆盖不足）**单独列出并归因**，
而不是让它淹没在 90%+ 的措辞差异噪声里。

---

## 四、本轮附带确认

| 项 | 结论 |
|----|------|
| 是否同一引擎 | ✅ 是，`D:\shuntian\src` 为唯一引擎源 |
| 是否存在引擎副本 | ❌ 无；qwen-agent 侧仅脚本，无引擎代码副本 |
| 1.9% 出处 | ✅ `proofread_dims.py` 的 `c in full_blob` 精确匹配 |
| 1.9% 可信度 | ❌ 方法性伪低值，不可作为覆盖指标 |
| 真实缺口 | ⚠️ 存在（如福德宫），需按语义单元重新评估 |

---

## 五、与 `D:\shuntian` 侧修复的关系

同日在 `D:\shuntian` 侧完成的修复（详见 `ZIWEI_COMPREHENSIVE_TEXT_GAP_20261012.md`）：

1. **自化解读接线缺陷**（`interpretation.py`）：`state._chart_ref` 不存在 → 自化解读 100% 丢失。已修为显式 `chart` 入参，实测 0/12 → 4/12。
2. **领域宫位静默丢失**（`domain_reading.py`）：`交友`/`仆役` 命名差异致学业/人际各丢一宫。已加 `PALACE_ALIAS` 回退。

> 该修复对 `proofread_dims.py` 的命中率**有正向影响**：
> 自化解读归位后，文章中断语含"自化"字样的条目（如 `文昌自化科`、`天机自化科`、
> `武曲天相自化科`）将从 ✗ 转为 ✓。
>
> 但**不会根本改变命中率量级**——因为主因是匹配方法，非引擎能力。

---

## 六、结论

1. **引擎同一**：qwen-agent 目录是千文千问工作现场，引擎即 `D:\shuntian`，无第二套。
2. **1.9% 证伪**：该数字源于整句子串精确匹配，是**方法性伪低值**；
   实测 5.7%，且同一方法下引擎已逐字输出了大量被判 ✗ 的断语。
3. **待办修正**：需要一套按语义单元评测的口径脚本，才能回答
   「引擎真实覆盖率是多少」以及「真实缺口在哪」。
