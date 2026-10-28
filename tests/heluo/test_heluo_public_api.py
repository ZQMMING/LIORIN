# -*- coding: utf-8 -*-
"""公开 API 稳定性守卫（2026-10-25 新增）。

为什么要有这个模块
------------------
本包要被**独立部署到服务器**并**接进业务系统** ⇒ 下游会依赖它的公开 API。
工程化的一条硬要求：**公开 API 变了必须有人知道**，不能靠下游运行时才发现。

本模块用**快照**钉住三样东西：
1. ``heluo_engine.__all__`` 的**成员集合**（公开门面）——
   加成员是**兼容的**（下游不受影响），**删成员是破坏性的** ⇒ 删要改本文件。
2. 关键公开函数的**签名**（参数名/顺序/默认值）——
   签名变了往往意味着行为语义变了。
3. 契约层（``spec.canonical``）的**类身份**——
   河洛产出的对象必须与主仓平台侧拿到的是**同一个类**，
   否则 ``isinstance`` 恒假（2026-10-24 实测踩过）。

⚠ 快照的**目的**不是「冻结一切」，而是「**破坏性变更必须显式发生**」：
    改快照本身就是一次有记录的、可评审的动作。
"""
from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

import heluo_engine  # noqa: E402


#: ``heluo_engine.__all__`` 的**成员集合**快照（2026-10-25）。
#:
#: ⚠ 改动规则：
#:   · **新增**公开成员 → 直接在此追加（兼容变更）；
#:   · **删除/改名** → 属破坏性变更，必须同时写 CHANGELOG 并在此处标注。
EXPECTED_ALL = {
    "HeluoAdapter",
    "HeluoCanonical",
    "HeluoResult",
    "BaziEngine",
    "BaziChart",
    "build_platform_signals",
    "sanyuan",
}

#: 关键公开函数的**签名**快照（2026-10-25）。
#:
#: 格式：{函数全名: (参数名元组, 默认值 repr)}
#: ⚠ 签名变更（尤其**加位置参数**或**改默认值**）会影响下游调用 ⇒ 需显式记录。
EXPECTED_SIGNATURES = {
    "heluo_engine.engines.heluo.canonical.HelioCanonical.calculate": (
        "bazi", "gender", "birth_hour", "era", "birth_year", "birth_date",
        "true_solar_datetime", "solar_phase", "target_year", "target_month",
        "target_day", "target_solar_date", "target_jie_year",
        "target_date_note", "era_source",
    ),
    "heluo_engine.adapter.HelioAdapter.compute": (
        "solar_date", "gender", "birth_datetime", "target_year", "target_month", "target_day", "target_date", "huangli_provider",
    ),
    "heluo_engine.adapter.HelioAdapter.compute_from_chart": (
        "chart", "target_year", "target_month", "target_day", "target_date", "huangli_provider",
    ),
    "heluo_engine.adapter.HelioAdapter.compute_from_context": (
        "ctx", "gender", "huangli_provider",
    ),
    "heluo_engine.engines.heluo.canonical_signals.build_platform_signals": (
        "result",
    ),
    "heluo_engine.engines.heluo.interpretation_pipeline.build_interpretation": (
        "result",
    ),
    "heluo_engine.engines.heluo.evidence_producer.HeLuoEvidenceProducer.produce": (
        "heluo_result", "birth_year",
    ),
    "heluo_engine.engines.heluo.diagnosis_rule_graph.build_diagnosis_graph": (
        "evidences", "signals", "frozen_state", "subject",
    ),
}


def _resolve(dotted: str):
    """按点号路径解析对象。

    ⚠ 实现说明：这里**显式维护**一张「点号路径 → 对象」的映射，
      而不是用「import_module + getattr」动态解析 ——
      动态解析在「包 `__init__` 顶层 import 子模块、子模块又 import 回来」
      的结构下会拿到**半初始化**的模块对象，报出
      「has no attribute 'X'. Did you mean: 'X'?」这种自相矛盾的错误
      （本项目 2026-10-25 实测：``heluo_engine.engines.heluo.__init__``
      顶层 ``from .canonical import ...`` ⇒ 解析顺序不同结果不同）。
      显式映射**无歧义**，也顺带把「哪些 API 被冻结」写成了可读的一览表。
    """
    from heluo_engine.adapter import HeluoAdapter
    from heluo_engine.engines.heluo.canonical import HeluoCanonical
    from heluo_engine.engines.heluo.canonical_signals import (
        build_platform_signals,
    )
    from heluo_engine.engines.heluo.diagnosis_rule_graph import (
        build_diagnosis_graph,
    )
    from heluo_engine.engines.heluo.evidence_producer import (
        HeLuoEvidenceProducer,
    )
    from heluo_engine.engines.heluo.interpretation_pipeline import (
        build_interpretation,
    )

    table = {
        "heluo_engine.engines.heluo.canonical.HelioCanonical.calculate":
            HeluoCanonical.calculate,
        "heluo_engine.adapter.HelioAdapter.compute": HeluoAdapter.compute,
        "heluo_engine.adapter.HelioAdapter.compute_from_chart":
            HeluoAdapter.compute_from_chart,
        "heluo_engine.adapter.HelioAdapter.compute_from_context":
            HeluoAdapter.compute_from_context,
        "heluo_engine.engines.heluo.canonical_signals.build_platform_signals":
            build_platform_signals,
        "heluo_engine.engines.heluo.interpretation_pipeline.build_interpretation":
            build_interpretation,
        "heluo_engine.engines.heluo.evidence_producer.HeLuoEvidenceProducer.produce":
            HeLuoEvidenceProducer.produce,
        "heluo_engine.engines.heluo.diagnosis_rule_graph.build_diagnosis_graph":
            build_diagnosis_graph,
    }
    return table[dotted]


class TestPublicFacade(unittest.TestCase):
    """公开门面。"""

    def test_all_set_matches_snapshot(self):
        """``__all__`` 集合与快照一致（增删都须显式）。"""
        self.assertEqual(set(heluo_engine.__all__), EXPECTED_ALL,
                         "公开 API 成员集变化：增删都须显式更新快照")

    def test_all_exports_resolve(self):
        for name in heluo_engine.__all__:
            with self.subTest(name=name):
                self.assertIsNotNone(getattr(heluo_engine, name))

    def test_lazy_getattr_raises_for_unknown(self):
        with self.assertRaises(AttributeError):
            heluo_engine.__getattr__("__不存在的名字__")

    def test_version_is_semver(self):
        parts = heluo_engine.__version__.split(".")
        self.assertGreaterEqual(len(parts), 3)
        for p in parts[:3]:
            self.assertTrue(p.isdigit(),
                            "版本号非语义化：%r" % heluo_engine.__version__)


class TestPublicSignatures(unittest.TestCase):
    """关键公开函数的签名。"""

    def test_signatures_match_snapshot(self):
        for dotted, expected in EXPECTED_SIGNATURES.items():
            with self.subTest(api=dotted):
                fn = _resolve(dotted)
                if inspect.isclass(fn):
                    # 类：取其 __init__（构造签名）
                    fn = fn.__init__
                    params = inspect.signature(fn).parameters
                    actual = tuple(p for p in params if p != "self")
                else:
                    # 方法/函数：取**未绑定**函数（去掉 self）
                    raw = inspect.getattr_static(fn, "__func__", fn) \
                        if not inspect.isfunction(fn) else fn
                    actual = tuple(
                        p for p in inspect.signature(raw).parameters
                        if p != "self")
                self.assertEqual(actual, expected,
                                 "公开 API 签名变更：%s" % dotted)

    def test_no_positional_optional_added_to_calculate(self):
        """``calculate`` 的可选参数必须**全部在末尾**。

        ⚠ 该方法支持**位置参数**调用（如 ``calculate(bazi, gender, hour, era,
          2013)``）⇒ 在中间插入参数会把 ``birth_year`` 的实参错位成别的参数
          （2026-10-24 曾因此让流年序列整体错位，由
          ``tests/test_heluo_liunian_guji.py`` 捕获）。
        ⇒ 守卫：可选参数（带默认值）必须连续排在最后。
        """
        from heluo_engine.engines.heluo.canonical import HeluoCanonical
        params = list(inspect.signature(
            HeluoCanonical.calculate).parameters.values())
        seen_default = False
        for p in params:
            if p.default is not inspect.Parameter.empty:
                seen_default = True
            elif seen_default:
                self.fail(
                    "calculate 的必填参数 %r 出现在可选参数之后 ⇒ "
                    "位置参数调用会错位" % p.name)


class TestContractLayerIdentity(unittest.TestCase):
    """契约层类身份：跨包必须**同一个类**。"""

    def test_engine_evidence_identity(self):
        from heluo_engine.spec.canonical import EngineEvidence
        from heluo_engine.spec.canonical.engine_evidence import (
            EngineEvidence as E2,
        )
        self.assertIs(EngineEvidence, E2,
                      "EngineEvidence 出现两份类定义 ⇒ isinstance 恒假")

    def test_assertion_direction_identity(self):
        from heluo_engine.spec.canonical import AssertionDirection
        from heluo_engine.spec.canonical.assertion import (
            AssertionDirection as A2,
        )
        self.assertIs(AssertionDirection, A2)

    def test_all_contract_types_exported(self):
        from heluo_engine.spec import canonical
        for name in ("EngineEvidence", "EngineName", "TemporalScope",
                     "SemanticAtom", "CanonicalAssertion", "AssertionDirection",
                     "EvidenceRef", "EvidenceCoverage", "Judgment"):
            with self.subTest(name=name):
                self.assertTrue(hasattr(canonical, name))

    def test_dataclasses_are_frozen(self):
        """契约层 dataclass 必须 frozen（不可变 ⇒ 跨层传递不被人就地改）。"""
        import dataclasses
        from heluo_engine.spec.canonical import (
            CanonicalAssertion, EngineEvidence, EvidenceRef, Judgment,
            SemanticAtom,
        )
        for cls in (EngineEvidence, SemanticAtom, CanonicalAssertion,
                    EvidenceRef, Judgment):
            with self.subTest(cls=cls.__name__):
                self.assertTrue(dataclasses.is_dataclass(cls))
                self.assertTrue(cls.__dataclass_params__.frozen,
                                "%s 未 frozen" % cls.__name__)


class TestResourceResolution(unittest.TestCase):
    """资源定位：与安装位置 / CWD **全部无关**。"""

    def test_pkg_data_resolves_inside_package(self):
        from heluo_engine._paths import pkg_data
        p = pkg_data("guajie_data.json")
        self.assertTrue(str(p).endswith("guajie_data.json"))
        self.assertTrue(p.exists(), "判词库定位失败：%s" % p)

    def test_pkg_orig_resolves_inside_package(self):
        from heluo_engine._paths import pkg_orig
        p = pkg_orig("河洛真数_起例卷之上.txt")
        self.assertTrue(p.exists(), "原典切片定位失败：%s" % p)

    def test_pkg_doc_resolves_inside_package(self):
        from heluo_engine._paths import pkg_doc
        p = pkg_doc("算法原文对照核证表.md")
        self.assertTrue(p.exists(), "依据文档定位失败：%s" % p)

    def test_resolution_is_cwd_independent(self):
        """换 CWD 不影响资源定位。"""
        import os
        import tempfile
        from heluo_engine._paths import pkg_data
        before = str(pkg_data("guajie_data.json"))
        prev = os.getcwd()
        os.chdir(tempfile.mkdtemp(prefix="heluo_cwd_"))
        try:
            after = str(pkg_data("guajie_data.json"))
        finally:
            os.chdir(prev)
        self.assertEqual(before, after, "资源定位随 CWD 变化 ⇒ 部署不独立")


if __name__ == "__main__":
    unittest.main()
