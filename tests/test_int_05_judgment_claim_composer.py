"""BZ-FNDR-15.16 ZIP-INT-05 Composer 契约测试.

S1~S6 验收门:
  S1: AC-ZP-{domain}-{conclusion} namespace
  S2: composer_version 进入 claim
  S3: provenance_marker 唯一来自 ProvenanceResolver (非 Composer 独立计算)
  S4: UNKNOWN/EVENT_ABSENT/NOT_EXECUTED/FAILED/SHIJIAN → 0 claim
  S5: DEGRADED/无 resolver → 0 claim
  S6: Chain-A 兼容: output 字段与 _build_claims_from_assertions 格式对齐
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))


class TestJudgmentClaimComposerS1(unittest.TestCase):
    """S1: namespace = AC-ZP-{domain}-{conclusion}."""

    def setUp(self):
        self.mock_resolver = MagicMock()
        from tongshu.governance.judgment_claim_composer import JudgmentClaimComposer
        self.composer = JudgmentClaimComposer(provenance_resolver=self.mock_resolver)
        # Fake DomainJudgment via simple object
        from dataclasses import dataclass, field
        from typing import List

        @dataclass(frozen=True)
        class _FakeDomainJudgment:
            domain: str
            conclusion: str
            reasoning: str = "fake"
            rule_refs: List[str] = field(default_factory=list)
            evidence_refs: List[str] = field(default_factory=list)
        self.FakeDJ = _FakeDomainJudgment

    def test_s1_namespace_format_ac_zp(self):
        """AC-ZP-{domain}-{conclusion} - semua domain valid harus产出."""
        synth = MagicMock()
        synth.wangshuai = self.FakeDJ(domain="WANGSHUAI", conclusion="STRONG")
        synth.geju = self.FakeDJ(domain="GEJU", conclusion="ESTABLISHED")
        synth.yongshen = self.FakeDJ(domain="YONGSHEN", conclusion="PRIMARY")
        synth.shishen = self.FakeDJ(domain="SHISHEN", conclusion="SEMANTIC_POSITIVE")
        synth.shijian = None  # S4 默认关

        claims = self.composer.compose(synth)
        ids = {c["claim_id"] for c in claims}
        self.assertEqual(ids, {
            "AC-ZP-wangshuai-strong",
            "AC-ZP-geju-established",
            "AC-ZP-yongshen-primary",
            "AC-ZP-shishen-semantic_positive",
        })


class TestJudgmentClaimComposerS2(unittest.TestCase):
    """S2: composer_version 进入 claim."""

    def test_s2_composer_version_present(self):
        from tongshu.governance.judgment_claim_composer import JudgmentClaimComposer
        from dataclasses import dataclass, field
        from typing import List

        @dataclass(frozen=True)
        class _FakeDJ:
            domain: str = "WANGSHUAI"
            conclusion: str = "STRONG"
            reasoning: str = "test"
            rule_refs: List[str] = field(default_factory=list)
            evidence_refs: List[str] = field(default_factory=list)

        composer = JudgmentClaimComposer(provenance_resolver=None)
        synth = MagicMock()
        synth.wangshuai = _FakeDJ()
        synth.geju = None
        synth.yongshen = None
        synth.shishen = None
        synth.shijian = None

        claims = composer.compose(synth)
        self.assertEqual(len(claims), 1)
        self.assertIn("composer_version", claims[0])
        self.assertEqual(claims[0]["composer_version"], "1.0.0")


class TestJudgmentClaimComposerS4(unittest.TestCase):
    """S4: UNKNOWN/EVENT_ABSENT/NOT_EXECUTED/FAILED/SHIJIAN → 0 claim (fail-closed)."""

    def setUp(self):
        from tongshu.governance.judgment_claim_composer import JudgmentClaimComposer
        from dataclasses import dataclass, field
        from typing import List

        @dataclass(frozen=True)
        class _FakeDJ:
            domain: str
            conclusion: str
            reasoning: str = "fake"
            rule_refs: List[str] = field(default_factory=list)
            evidence_refs: List[str] = field(default_factory=list)
        self.FakeDJ = _FakeDJ

        self.composer = JudgmentClaimComposer(provenance_resolver=None)

    def test_s4_unknown_blocks_claim(self):
        synth = MagicMock()
        synth.wangshuai = self.FakeDJ(domain="WANGSHUAI", conclusion="UNKNOWN")
        synth.geju = self.FakeDJ(domain="GEJU", conclusion="UNKNOWN")
        synth.yongshen = None
        synth.shishen = None
        synth.shijian = None
        self.assertEqual(self.composer.compose(synth), [])

    def test_s4_event_absent_blocks_shijian_claim(self):
        """15.14 audit: SHIJIAN EVENT_ABSENT = fail-open 伪判定, 必须 0 claim."""
        synth = MagicMock()
        synth.wangshuai = None
        synth.geju = None
        synth.yongshen = None
        synth.shishen = None
        synth.shijian = self.FakeDJ(domain="SHIJIAN", conclusion="EVENT_ABSENT")
        self.assertEqual(self.composer.compose(synth), [])

    def test_s4_shijian_event_exist_released_after_method_audit(self):
        """2026-11-10 method audit PASS (ZIPING_CLASSIC_RULES §二十二):
        方法链 V7.186-193 已入生产(流年冲命局/太岁冲运, 锚 FAN_YIN_FU_YIN.001
        +SUI_YUN_BING_LIN.001) → 域级封闭解除, EVENT_EXIST 可产 1 claim;
        claim 文本须带「未核验」免责措辞 (宁缺勿猜: 只报触发符号, 不判吉凶/应期)."""
        synth = MagicMock()
        synth.wangshuai = None
        synth.geju = None
        synth.yongshen = None
        synth.shishen = None
        synth.shijian = self.FakeDJ(
            domain="SHIJIAN", conclusion="EVENT_EXIST",
            reasoning="触发 未丑(流年冲大运)；冲为事件触发符号，实际作用 p0 明示未核验（不判吉凶/应期）")
        claims = self.composer.compose(synth)
        ids = [c["claim_id"] for c in claims]
        self.assertIn("AC-ZP-shijian-event_exist", ids,
                      "method audit PASS 后 SHIJIAN EVENT_EXIST 必须放行产 claim")
        shijian_claim = next(c for c in claims if c["domain"] == "SHIJIAN")
        self.assertIn("未核验", shijian_claim["claim"],
                      "SHIJIAN claim 必须保留「未核验」免责措辞")

    def test_s4_mixed_unknown_partial_claim(self):
        """部分域 UNKNOWN → 只 valid 域产 claim."""
        synth = MagicMock()
        synth.wangshuai = self.FakeDJ(domain="WANGSHUAI", conclusion="STRONG")
        synth.geju = self.FakeDJ(domain="GEJU", conclusion="UNKNOWN")
        synth.yongshen = self.FakeDJ(domain="YONGSHEN", conclusion="PRIMARY")
        synth.shishen = None
        synth.shijian = None
        claims = self.composer.compose(synth)
        self.assertEqual(len(claims), 2)
        ids = {c["claim_id"] for c in claims}
        self.assertIn("AC-ZP-wangshuai-strong", ids)
        self.assertIn("AC-ZP-yongshen-primary", ids)
        self.assertNotIn("AC-ZP-geju-unknown", ids)


class TestJudgmentClaimComposerS3(unittest.TestCase):
    """S3: provenance_marker 唯一来自 ProvenanceResolver, 非 Composer 独立计算."""

    def test_s3_marker_from_resolver_only(self):
        from tongshu.governance.judgment_claim_composer import JudgmentClaimComposer
        from dataclasses import dataclass, field
        from typing import List

        @dataclass(frozen=True)
        class _FakeDJ:
            domain: str
            conclusion: str
            reasoning: str = "test"
            rule_refs: List[str] = field(default_factory=list)
            evidence_refs: List[str] = field(default_factory=list)
            signal_ids: List[str] = field(default_factory=list)

        # Mock resolver + index 完全模拟真实 API 调用链
        mock_resolver = MagicMock()
        mock_index = MagicMock()
        mock_index.by_id = {"E-DTS-001": MagicMock(rel_posix="some/path.json")}
        mock_resolver.index = mock_index

        resolved_mock = MagicMock()
        resolved_mock.to_claim_mark.return_value = "PROVENANCE-PENDING"
        mock_resolver.resolve.return_value = resolved_mock

        composer = JudgmentClaimComposer(provenance_resolver=mock_resolver)
        synth = MagicMock()
        synth.wangshuai = _FakeDJ(domain="WANGSHUAI", conclusion="STRONG",
                                  evidence_refs=["E-DTS-001"])
        synth.geju = None
        synth.yongshen = None
        synth.shishen = None
        synth.shijian = None

        claims = composer.compose(synth)
        self.assertEqual(claims[0]["provenance_marker"], "PROVENANCE-PENDING")
        # S3: Composer 调用了 resolver.resolve(rel_path) 一次
        mock_resolver.resolve.assert_called_once_with("some/path.json")


class TestJudgmentClaimComposerS5(unittest.TestCase):
    """S5: 无 resolver 或 resolver = None → 0 provenance_marker (Composer 不伪造)."""

    def test_s5_no_resolver_marker_none(self):
        from tongshu.governance.judgment_claim_composer import JudgmentClaimComposer
        from dataclasses import dataclass, field
        from typing import List

        @dataclass(frozen=True)
        class _FakeDJ:
            domain: str = "WANGSHUAI"
            conclusion: str = "STRONG"
            reasoning: str = "test"
            rule_refs: List[str] = field(default_factory=list)
            evidence_refs: List[str] = field(default_factory=list)

        composer = JudgmentClaimComposer(provenance_resolver=None)
        synth = MagicMock()
        synth.wangshuai = _FakeDJ()
        synth.geju = None
        synth.yongshen = None
        synth.shishen = None
        synth.shijian = None

        claims = composer.compose(synth)
        # Composer 仍然产 claim (domain valid), 但 provenance_marker = None
        self.assertEqual(len(claims), 1)
        self.assertIsNone(claims[0]["provenance_marker"])


class TestJudgmentClaimComposerEmpty(unittest.TestCase):
    """边界: None synthesis / 全 None domains → 空列表."""

    def test_none_synthesis_returns_empty(self):
        from tongshu.governance.judgment_claim_composer import JudgmentClaimComposer
        composer = JudgmentClaimComposer(provenance_resolver=None)
        self.assertEqual(composer.compose(None), [])

    def test_all_none_domains_returns_empty(self):
        from tongshu.governance.judgment_claim_composer import JudgmentClaimComposer
        composer = JudgmentClaimComposer(provenance_resolver=None)
        synth = MagicMock()
        synth.wangshuai = None
        synth.geju = None
        synth.yongshen = None
        synth.shishen = None
        synth.shijian = None
        self.assertEqual(composer.compose(synth), [])


class TestJudgmentClaimComposerRealSynthesis(unittest.TestCase):
    """集成测试: 真实 JudgmentSynthesis + 真实 ProvenanceResolver (树B)."""

    def test_real_synthesis_real_resolver_end_to_end(self):
        """完整链路: 真实 JudgmentSynthesis + 真实 ProvenanceResolver → AC-ZP-* claims."""
        from tongshu.governance.evidence_index import EvidenceIndex
        from tongshu.governance.provenance_resolver import ProvenanceResolver
        from tongshu.governance.judgment_claim_composer import JudgmentClaimComposer
        from tongshu.reasoning.judgment import (
            JudgmentSynthesis, DomainJudgment, JudgmentDomain, JudgmentConclusion
        )

        corpus_root = _REPO_ROOT / "data" / "evidence"
        if not corpus_root.exists():
            self.skipTest("data/evidence not available")

        index = EvidenceIndex.build(corpus_root, tree="corpus_base")
        resolver = ProvenanceResolver(index)
        composer = JudgmentClaimComposer(provenance_resolver=resolver)

        # Build real JudgmentSynthesis: 4 domain valid + SHIJIAN EVENT_EXIST (will be blocked by S4)
        synth = JudgmentSynthesis(
            wangshuai=DomainJudgment(
                domain=JudgmentDomain.WANGSHUAI,
                conclusion=JudgmentConclusion.STRONG,
                reasoning="得令得势得地",
                evidence_refs=[],
            ),
            geju=DomainJudgment(
                domain=JudgmentDomain.GEJU,
                conclusion=JudgmentConclusion.ESTABLISHED,
                reasoning="建禄格成立",
                evidence_refs=[],
            ),
            yongshen=DomainJudgment(
                domain=JudgmentDomain.YONGSHEN,
                conclusion=JudgmentConclusion.PRIMARY,
                reasoning="扶抑格用神",
                evidence_refs=[],
            ),
            shishen=DomainJudgment(
                domain=JudgmentDomain.SHISHEN,
                conclusion=JudgmentConclusion.SEMANTIC_POSITIVE,
                reasoning="食神制杀吉",
                evidence_refs=[],
            ),
            shijian=DomainJudgment(  # 2026-11-10 method audit PASS → 域级封闭解除
                domain=JudgmentDomain.SHIJIAN,
                conclusion=JudgmentConclusion.EVENT_EXIST,
                reasoning="触发 子午(流年冲大运)；冲为事件触发符号，实际作用 p0 明示未核验（不判吉凶/应期）",
                evidence_refs=[],
            ),
        )
        claims = composer.compose(synth)

        # 4 valid domains + SHIJIAN EVENT_EXIST (released after method audit) → 5 claims
        self.assertEqual(len(claims), 5)
        ids = {c["claim_id"] for c in claims}
        self.assertIn("AC-ZP-wangshuai-strong", ids)
        self.assertIn("AC-ZP-geju-established", ids)
        self.assertIn("AC-ZP-yongshen-primary", ids)
        self.assertIn("AC-ZP-shishen-semantic_positive", ids)
        # S4 域级已放行; 结论级 fail-closed 不变 (EVENT_ABSENT/UNKNOWN 仍 0 claim)
        self.assertIn("AC-ZP-shijian-event_exist", ids)

        # All claims have composer_version (S2)
        for c in claims:
            self.assertEqual(c["composer_version"], "1.0.0")
            # source_layers = ZI_PING (matches Chain-A engine tag)
            self.assertEqual(c["source_layers"], ["ZI_PING"])


if __name__ == "__main__":
    unittest.main()
