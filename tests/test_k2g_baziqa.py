#!/usr/bin/env python3
"""
BaziQA 测试套件
用于验证Shuntian K2G系统性能
"""
import pytest
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any

# 数据集路径
DATASET_PATH = Path('./docs/k2g/datasets/baziqa_2021.json')

class TestBaziQA:
    """BaziQA基准测试"""
    
    @pytest.fixture(autouse=True)
    def load_dataset(self):
        """加载数据集"""
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            self.dataset = yaml.safe_load(f)
        self.questions = self.dataset.get('data', [])
        print(f"\n加载数据集: {len(self.questions)} 题")
    
    def test_dataset_integrity(self):
        """测试数据集完整性"""
        assert len(self.questions) > 0, "数据集为空"
        assert 'schema_version' in self.dataset
        assert 'total_count' in self.dataset
        assert self.dataset['total_count'] == len(self.questions)
    
    def test_question_structure(self):
        """测试题目结构"""
        for q in self.questions:
            assert 'question_id' in q, f"缺少question_id: {q}"
            assert 'year' in q, f"缺少year: {q}"
            assert 'answer' in q, f"缺少answer: {q}"
            assert 'options' in q, f"缺少options: {q}"
            assert len(q['options']) == 4, f"选项数量不对: {q['question_id']}"
            assert set(q['options'].keys()) == {'A', 'B', 'C', 'D'}, f"选项键不对: {q['question_id']}"
    
    def test_answer_validity(self):
        """测试答案有效性"""
        for q in self.questions:
            assert q['answer'] in ['A', 'B', 'C', 'D'], f"无效答案: {q['question_id']} = {q['answer']}"
    
    def test_category_distribution(self):
        """测试类别分布"""
        categories = {}
        for q in self.questions:
            cat = q.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        # 至少有5个不同类别
        assert len(categories) >= 5, f"类别太少: {categories}"
        print(f"类别分布: {categories}")
    
    def test_year_distribution(self):
        """测试年份分布"""
        years = {}
        for q in self.questions:
            y = q.get('year', 0)
            years[y] = years.get(y, 0) + 1
        
        assert 2021 in years, "缺少2021年数据"
        print(f"年份分布: {years}")

class TestShuntianBenchmark:
    """顺天系统Benchmark测试"""
    
    @pytest.fixture(autouse=True)
    def load_system(self):
        """加载系统"""
        try:
            from tongshu.k2g.registry_loader import load_k2g_registry
            self.loader = load_k2g_registry()
            self.loaded = True
        except ImportError:
            self.loaded = False
            pytest.skip("K2G模块未安装")
    
    def test_registry_loaded(self):
        """测试Registry加载"""
        assert self.loaded, "K2G模块未加载"
        
        counts = self.loader.get_all_counts()
        assert counts['semantics'] >= 100, f"SEMANTIC不足: {counts['semantics']}"
        assert counts['relations'] >= 20, f"RELATION不足: {counts['relations']}"
        assert counts['golden'] >= 250, f"GOLDEN不足: {counts['golden']}"
    
    def test_baziqa_integration_ready(self):
        """测试BaziQA集成准备"""
        # 检查是否有测试接口
        test_path = Path('./backend/tests/test_k2g_baziqa.py')
        if test_path.exists():
            print("BaziQA测试文件已存在")
        else:
            print("建议创建: test_k2g_baziqa.py")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
