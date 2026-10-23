# 河洛引擎（Heluo Engine）

基于《河洛真数》（起例卷、易卦释义、诗断秘诀）的独立推命引擎。以出生四柱（八字排盘）配合真太阳时，推卦象、化工、元气、节候、大运流年、卦辞断语与现代释义。

## 目录结构

一切都在 **`src/heluo_engine/`** 一个文件夹下 —— 独立顶层包，与主仓 `tongshu`
命名空间完全隔离，可 `pip install` 到服务器独立运行（**零路径绑定**）。

```
src/heluo_engine/
  __init__.py               对外 API 门面（惰性导出）
  _paths.py                 ★ 统一资源定位（importlib.resources / __file__ 双通道）
  adapter.py                HeluoAdapter（三入口）
  data/                     ★ 运行时数据（随包）
    guajie_data.json          卦辞/断语/邵曰（64卦×6爻，原典直录）
    guajie_jingyi.json        现代语义精义（706 单元）
    kuozhan_duanyu.json       扩展断语
    locations.json            出生地点注册表
    canping/                  参评诗断语料
  orig/                     ★ 原典切片（判词与语料的逐字上游）
  docs/                     ★ 依据文档（定案/裁决/核定/对照表）
  engines/
    heluo/                 # 河洛引擎核心（37 模块）
      canonical.py         # 主入口 HeluoCanonical.calculate（编排各步）
      input.py             # 输入构造（四柱/真太阳时）
      hexagram.py          # 卦象
      hua_gong.py          # 化工（NORMAL/REVERSE/RESCUED/RESTRAINED/UNRESOLVED）
      yuan_qi.py           # 元气层
      jiehhou.py           # 节候卦（节气回溯）
      timeline_yun.py      # 大运/流年/流月/流日/流时爻位值运（含 Timeline 数据类）
      guajie.py            # 卦辞/断语/诗断
      heluo_lunar_bridge.py  # H9b 河洛×黄历桥接（流日段黄历标注：注入优先/lunar_python 兜底）
      yi_interpreter.py    # 流年卦断语（P1 解卦层）
      diagnosis_rule_graph.py  # 诊断规则图
      frozen_state.py      # 冻结态输出
      relationship/        # 关系（互体/反体/对体/纳音福力）
    bazi_engine.py         # 八字排盘（上游：排四柱）
    bazi_adapter.py
    time_resolver.py       # 时间解析上游
    time/                  # 真太阳时（均时差/经度/时区/换日）
    yi/                    # 易经卦爻辞结构
  facts/  reasoning/  spec/  # 干支事实、十神、规范
tests/heluo/               # 河洛单元测试
tests/cross_repo/          # 跨仓接线守卫（须在主仓环境跑；独立包内自动跳过）
docs/heluo/                # 引擎说明（HELUO_ENGINE.md 为主文档）
```

## 入口

```python
from heluo_engine import HeluoAdapter

r = HeluoAdapter().compute((1983, 11, 3, 12), gender="male", target_date="2026-10-23")
r.prenatal.hexagram_name   # 风山渐
r.yuantang.yuantang        # 初六
r.postnatal.hexagram_name  # 火风鼎
```

`HeluoAdapter` 提供三个入口：

- `compute(...)`：直接给出生时间、地点，内部走真太阳时（TimeResolver）后排盘计算。
- `compute_from_chart(...)`：消费已排好的四柱（含真太阳时时柱）。
- `compute_from_context(...)`：消费完整计算上下文。

> 流时卦按设计剥离，不纳入计算。大运/流年/流月由引擎自算；流月以节气为锚。

### 惰性化（H10 定稿方案）

只算目标点，其余仅元数据：

- `compute(..., target_year, target_month, target_day)`：目标流年 1 套流年卦、
  目标年 12 流月卦（顶层 `timeline.monthly_hexagrams`，完整卦象，不再嵌套 yearly）、
  目标月 1 个流日本卦（顶层 `timeline.daily_hexagram`：`base_hex` + `daily_yao`）。
- 全部流年元数据（year/age/ganzhi，无卦象）在 `timeline.yearly_meta`。
- 不传 target：兼容全量（静态层一次算完）。

性能（1980-06-22 庚申男，稳态）：**带 target 惰性 ~24ms/案例** vs 无 target 全量 ~937ms，
省约 97% 算力。

### 流日卦规则分疏（H10b：节气为界，均匀分配）

古籍并存两套操作规则，均从当月"节"交接时刻起算，**按实际节气间隔均匀切段、
不可机械固定每段日数**（节气长度不均等，约 29~31 日）：

- `rule="hou5"`（五日一变·候卦系统，默认）：6 段（初爻→上爻），每爻管约 5 日，
  段边界 = 节时刻 + k×(下节-节)/6，含时刻标注。
- `rule="gua6"`（六日一变·卦气系统）：5 段（每卦管约 6 日），
  汉易"一爻一日、一卦六日"模型，段边界 = 节时刻 + k×(下节-节)/5。

段字段：`day_from/day_to`（月内日序）、`date_from/date_to`（含节气时刻）、
`jie_span_days`（实际节气间隔天数留痕）。无节气数据时退化为机械相对分段（兼容旧调用）。

### 黄历桥接（H9b）

流日应期段（guajie.liuri_lunar）挂载黄历标注（农历/日柱/纳音/节气/宜忌）。数据源：

- **注入优先**：`adapter.compute(..., huangli_provider=fn)`，fn 接收公历日期 `YYYY-MM-DD`、返回主工作区黄历引擎（HuangliEngine.get_day）产物 dict，字段映射见 `heluo_lunar_bridge.annotate_day`；标注 `source=huangli_engine`。
- **lunar_python 兜底**：不传 provider 时独立自产（农历/日柱/纳音/节气），标注 `source=lunar_python`，保证引擎独立可跑。

```python
def huangli_provider(solar_date: str) -> dict | None:
    return huangli_engine.get_day(date.fromisoformat(solar_date)).__dict__
r = HeluoAdapter().compute((1980, 6, 22, 10), gender="male",
                           target_year=2027, target_month=6, target_day=15,
                           huangli_provider=huangli_provider)
r.guajie["liuri_lunar"]  # {'solar_date': '2027-05-16', 'lunar': '十一月 初十', ...}
```

流日定位段取 `date_from`（节气对齐段首日）标注；未命中流日段时 `liuri_lunar` 为 None。

## 安装

```bash
pip install .          # 服务器部署：装完即可用，与仓库位置/运行目录无关
# 开发态
pip install -e .
```

第三方依赖：`sxtwl`（节气）、`lunar_python`、`chinese-calendar`、`pyyaml`、
`jsonschema`、`pydantic`。

> **独立部署**：本包不再依赖主仓仓库、不依赖 `tongshu` 命名空间、
> 不依赖特定目录层级或 CWD —— 判词库/原典/依据文档全部**随包分发**，
> 由 `heluo_engine._paths` 按包定位。
> 详见 `docs/heluo/河洛引擎包结构与部署_20261024.md`。

## 运行测试

```bash
# Windows PowerShell
$env:PYTHONPATH = "src"
python -m pytest tests/ -q
```

## 数据与依据

- `heluo_engine/orig/`：《河洛真数》起例卷、《易卦释义》、《诗断秘诀》原文切片
  —— 判词与语料的**逐字上游**（守卫会逐字回查）。
- `heluo_engine/data/guajie_data.json`：卦辞/爻辞/象曰/断语/邵曰（64卦×6爻）。
- `heluo_engine/data/guajie_jingyi.json`：卦辞现代精义（706 单元）。
- `heluo_engine/docs/算法原文对照核证表.md`：算法与原典逐句对照核证。
- `heluo_engine/docs/` 其余：定案 / 裁决 / 核定 / 对照表（判据的证据链）。
