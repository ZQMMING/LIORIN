"""子平引擎族 · qiongtong_baojian（QIONGTONG_BAOJIAN）· V2.2.2 FINAL。
共享计算层 engines/common（L0 映射/事实管线/EngineResult）；
Rule/Evidence 由 engines/yuhai_ziping 参数化实现（RuleEngine/EvidenceRegistry(engine=...)）。
Phase 6+ 各引擎自有派生（格局/旺衰/气势/病药等）在本引擎目录内实现。"""

ENGINE_ID = "QIONGTONG_BAOJIAN"
ENGINE_VERSION = "0.1.0"
CONTRACT_VERSION = "0.1.0"
__all__ = ["ENGINE_ID", "ENGINE_VERSION", "CONTRACT_VERSION"]
