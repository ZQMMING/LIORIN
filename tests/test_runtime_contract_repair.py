"""Runtime wiring regressions; no Golden expectations or strength thresholds changed."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.common import yongyao_resolve as medicine
from p0_v2 import bazi_gate


class RuntimeContractTests(unittest.TestCase):
    def test_each_disease_routes_to_its_controlling_element(self):
        # Independent five-element oracle: medicine must control the disease.
        controls = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
        for disease in controls:
            with self.subTest(disease=disease):
                facts = {'daymaster_element': '木', 'p1_bing': {'bing_list': [
                    {'bing_wx': disease, 'severity': 3}]}}
                with patch.object(medicine, '_geju_xiji_ws', return_value=([], [])):
                    result = medicine._yongshen_routing(facts, {})
                self.assertEqual(controls[result['winner_shen']], disease)

    def test_natal_medicine_consumes_converted_secondary_diseases(self):
        original = bazi_gate.resolve_yongyao
        captured = []

        def observe(facts, debate, climate, **kwargs):
            captured.append((debate, kwargs))
            return original(facts, debate, climate, **kwargs)

        with patch.object(bazi_gate, 'resolve_yongyao', side_effect=observe):
            result = bazi_gate.paipan('丁酉 乙巳 丁丑 丙午')
        self.assertTrue(result['zhuangui']['converted_medicine'])
        self.assertEqual(captured[0][0], result['zhuangui'])
        self.assertEqual(captured[0][1].get('bing_list'), result['bing_list'])

    def test_explicit_diseases_override_stale_fact_snapshot(self):
        facts = {'daymaster_element': '木', 'p1_bing': {'bing_list': [
            {'bing_wx': '水', 'severity': 4}]}}
        with patch.object(medicine, '_geju_xiji_ws', return_value=([], [])):
            result = medicine._yongshen_routing(
                facts, {}, bing_list=[{'bing_wx': '土', 'severity': 3}])
            empty = medicine._yongshen_routing(facts, {}, bing_list=[])
        self.assertEqual(result['winner_shen'], '木')
        self.assertIsNone(empty['winner_shen'])


if __name__ == '__main__':
    unittest.main()
