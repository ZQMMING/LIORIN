"""
K2G Registry 数据加载器
从YAML文件加载所有Registry数据到内存
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import os


# 默认Registry路径：环境变量优先，其次项目相对路径（路径独立性）
_PROJECT_K2G_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'docs' / 'k2g'
DEFAULT_REGISTRY_PATH = os.environ.get(
    'K2G_REGISTRY_PATH',
    str(_PROJECT_K2G_DIR) if _PROJECT_K2G_DIR.exists() else 'docs/k2g',
)


@dataclass
class RegistryLoader:
    """Registry数据加载器"""
    
    registry_path: Path
    
    def __post_init__(self):
        # 确保路径存在（支持Windows和POSIX路径）
        path_str = str(self.registry_path).replace('\\', '/')
        if not Path(path_str).exists():
            # 尝试原始路径
            if not self.registry_path.exists():
                raise FileNotFoundError(f"Registry path not found: {self.registry_path}")
    
    def load_semantics(self) -> List[Dict]:
        """加载语义注册表"""
        path = self.registry_path / 'semantic' / 'semantic_registry.yaml'
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        return data.get('semantics', [])
    
    def load_relations(self) -> List[Dict]:
        """加载关系注册表"""
        path = self.registry_path / 'relation' / 'relation_registry.yaml'
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        return data.get('relations', [])
    
    def load_states(self) -> List[Dict]:
        """加载状态模板"""
        path = self.registry_path / 'state' / 'state_template_registry.yaml'
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        return data.get('state_templates', [])
    
    def load_safety(self) -> List[Dict]:
        """加载安全规则"""
        path = self.registry_path / 'safety' / 'safety_registry.yaml'
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        return data.get('safety_rules', [])
    
    def load_core(self) -> Dict:
        """加载核心注册表"""
        path = self.registry_path / 'core_registries.yaml'
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding='utf-8'))
    
    def load_golden(self) -> Dict:
        """加载黄金数据集"""
        path = self.registry_path / 'K2G_GOLDEN_DATASET_v3.json'
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding='utf-8'))
    
    def get_all_counts(self) -> Dict[str, int]:
        """获取所有Registry条目数"""
        return {
            'semantics': len(self.load_semantics()),
            'relations': len(self.load_relations()),
            'states': len(self.load_states()),
            'safety': len(self.load_safety()),
            'mappings': len(self.load_core().get('mappings', [])),
            'daily_guidance': len(self.load_core().get('daily_guidance', [])),
            'expressions': len(self.load_core().get('expressions', [])),
            'golden': self.load_golden().get('total_count', 0),
        }


def load_k2g_registry(path: Optional[str] = None) -> RegistryLoader:
    """工厂函数：创建Registry加载器"""
    if path is None:
        path = DEFAULT_REGISTRY_PATH
    # 规范化路径
    path = path.replace('\\', '/').replace('//', '/')
    return RegistryLoader(Path(path))
