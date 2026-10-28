# 贡献指南

## 环境

```bash
python -m pip install -e ".[dev]"
```

## 提交前必跑

```bash
python -m pytest -q                       # 全量测试
python -m ruff check src tests tools      # 静态检查
python -m ruff format --check src tests tools
```

## 本项目的**硬纪律**（违反即回退）

### 1. 原典录入逐字照抄
繁简 / 异体 / OCR 讹字**一仍其旧**。订正必须**单独立据**并留档
（`orig/*_校记.md`），不得直接改字。

### 2. 判据只给「吉 / 凶 / 不判」，绝不给 0–1 分数
分数是**自拟**的，无原典依据。已作废的自拟分数函数
（`get_base_factors` / `calculate_element_modifier` /
`_hexagram_base_score` / `_year_cycle_factor`）**不得复活**
（守卫：`tests/heluo/test_heluo_interpretation_pipeline.py`）。

### 3. 原典未言 ⇒ 不判
「没命中吉辞」**推不出**「凶」。无门槛时一律 `passed=None`。

### 4. 缺失被当成正常，比答错更坏
任何降级/失败**必须留痕**（`warnings` / `error` 字段），
不得静默留空。

### 5. 守卫要防「恒绿陷阱」
- 变异锚点必须打在**盘上必然出现**的路径，或**静态可检**的位置；
- 禁用函数检测用 **AST**（文本搜索会命中定义与 docstring ⇒ 假阳性）；
- 断言钉**结构与计数**，不只钉「关键词存在」。

## 改动类型与守则

| 改动 | 要求 |
|---|---|
| 公开 API 增删 | 更新 `tests/heluo/test_heluo_public_api.py` 的快照 + CHANGELOG |
| 公开 API 签名变更 | 同上（签名变更会影响下游调用） |
| 判据口径变更 | 必须附**原典出处**（行号 + 原文摘录）+ 校记 |
| 新增依赖 | 在 `pyproject` 的 `dependencies` 声明，并说明**为什么必需** |
| 原典切片扩充 | 同步更新 `orig/*_校记.md` 的定位表 |

## 提交信息

```
<type>(heluo): <一句话>

<正文：为什么改、依据是什么、影响面>
```

常用 type：`feat` / `fix` / `docs` / `test` / `chore` / `refactor`。
