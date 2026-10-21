# 河洛引擎（Heluo Engine）

基于《河洛真数》（起例卷、易卦释义、诗断秘诀）的独立推命引擎。以出生四柱（八字排盘）配合真太阳时，推卦象、化工、元气、节候、大运流年、卦辞断语与现代释义。

## 目录结构

```
src/tongshu/
  engines/
    heluo/                 # 河洛引擎核心
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
    heluo_adapter.py       # 对外适配器 HeluoAdapter（三入口）
    bazi_engine.py         # 八字排盘（上游：排四柱）
    bazi_adapter.py
    time/                  # 真太阳时（均时差/经度/时区/换日）
    yi/                    # 易经卦爻辞结构
  facts/  reasoning/  spec/  # 干支事实、十神、规范
data/heluo/                # 原典数据（guajie_jingyi、guajie_raw、核证表等）
tests/heluo/               # 河洛单元测试
docs/heluo/HELUO_ENGINE.md # 引擎说明
```

## 入口

`HeluoAdapter` 提供三个入口：

- `compute(...)`：直接给出生时间、地点，内部走真太阳时（TimeResolver）后排盘计算。
- `compute_from_chart(...)`：消费已排好的四柱（含真太阳时时柱）。
- `compute_from_context(...)`：消费完整计算上下文。

> 流时卦按设计剥离，不纳入计算。大运/流年/流月由引擎自算；流月以节气为锚。

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
pip install -e .
# 或按 pyproject.toml 安装依赖
```

第三方依赖：`sxtwl`（节气）、`lunar_python`、`chinese-calendar`、`pyyaml`、`pydantic`。

## 运行测试

```bash
# Windows PowerShell
$env:PYTHONPATH = "src"
python -m pytest tests/heluo -q
```

## 数据与依据

- `data/heluo/guajie_raw/`：《河洛真数》起例卷、易卦释义、诗断秘诀原文。
- `data/heluo/guajie_jingyi.json`：卦辞现代精义（706 单元）。
- `data/heluo/算法原文对照核证表.md`：算法与原典逐句对照核证。
