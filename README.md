# 紫微斗数引擎 (Ziwei Doushu Engine)

紫微斗数引擎的**独立迁移分支**。三层架构：**算层 → 辨层 → 解层**；南北两派（三合派 + 钦天派）并行，不融合 / 不投票。

## 环境准备 (Setup)
引擎为 **Python + Node.js 混合**：紫微排盘依赖 npm 包 `iztro`（经子进程调用）。
```bash
npm install   # 安装 node_modules/iztro（Node 依赖，勿提交 node_modules）
uv sync       # 安装 Python 依赖并注册 tongshu 包
```

## 运行测试
```bash
uv run pytest tests/ -k ziwei
```

## 目录结构
- `src/tongshu/engines/ziwei/` — 引擎核心（`rules/` 规则层、`rules/qintian/` 钦天派、`z14/` 证据采集、`dataset_bridge`、`evidence_producer`）
- `src/tongshu/engines/ziwei_engine.py` / `ziwei_dependency_adapter.py` / `ziwei_adapter.py` / `ziwei_method_profile.py` / `ziwei_palace_resolution.py` — 引擎入口与适配层
- `src/tongshu/{spec,reasoning,assertion,facts}` + `engines/{yi,bazi,huangli}` — 引擎运行所需的**真实共享依赖**（紫微引擎导入它们）
- `tests/` — 紫微测试集（`test_ziwei*` + `spec/test_vertical_slice_ziwei.py`）
- `data/`、`cases/` — 紫微数据与 golden 案例
- `scripts/` — 紫微审计 / 回放 / 校验工具
- `docs/audit/ZIWEI*`、`docs/bots/BOT-ZIWEI/` — 紫微审计与交付文档

## 边界说明
本分支**仅**包含紫微引擎及其真实依赖。其他命理引擎（河洛 / 盲派 / 子平 / 梅花）、前端、后端应用、`node_modules` 等均不属于本分支（`node_modules` 由 `npm install` 生成）。
