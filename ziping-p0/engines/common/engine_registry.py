"""子平引擎族注册表（引擎无关）。

统一命名空间：
- 缩写（registry 文件后缀 / RuleEngine(engine=) / FactsBuilder(engine=)）
- 目录名（engines/<dir>/）
- ENGINE_ID（contract.engine / EngineResult.engine）
"""

from __future__ import annotations

# 缩写 → ENGINE_ID
ENGINE_ID_MAP = {
    "yhzp": "YUHAI_ZIPING",
    "pzzq": "ZIPING_ZHENQUAN",
    "dts": "DITIANSUI",
    "qtbj": "QIONGTONG_BAOJIAN",
    "smth": "SANMING_TONGHUI",
    "sftk": "SHENFENG_TONGKAO",
}

# 缩写 → 引擎目录名
ENGINE_DIR_MAP = {
    "yhzp": "yuhai_ziping",
    "pzzq": "ziping_zhenquan",
    "dts": "ditiansui",
    "qtbj": "qiongtong_baojian",
    "smth": "sanming_tonghui",
    "sftk": "shenfeng_tongkao",
}
