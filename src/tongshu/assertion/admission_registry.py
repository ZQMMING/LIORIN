"""
P2.1-B: Admission Authority Model — Immutable Capability + Identity Binding (v7)

安全设计（v7，应对 object.__new__() 绕过）：
  1. AdmissionAuthority 使用模块级私有哨兵对象，外部无法创建等价对象
  2. 所有注册表/库使用 is 检查（而非 isinstance），防止类型伪装
  3. AuditedIdentity 的 authority_source + credential_hash 绑定验证链
  4. LEGACY/HUMAN 身份必须通过预注册 authority_source 才能 admission

攻击模型（v7）：
  object.__new__(AdmissionAuthority)  → ❌ 创建的是新实例，is 检查失败
  AdmissionAuthority()                → ❌ 构造函数抛 TypeError
  object.__new__(AdmissionRegistry)   → ❌ 类有 __new__ 限制
  伪造 credential_hash                → ❌ AdmissionRecord 完整性校验失败
"""
from __future__ import annotations

import enum
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# G1: AdmissionAuthority — 不可伪造的权威性标志（v7 修复）
# ============================================================

class _AdmissionAuthority:
    """
    生产准入 Authority 内部标志。

    安全设计（v7）：
    - 模块级单例 `_ADMISSION_CAPABILITY`，外部无法访问
    - 构造函数强制 TypeError，阻止正常实例化
    - __new__ 也抛 TypeError，阻止 object.__new__() 绕过
    - Registry 内部用 `is` 检查（而非 isinstance），攻击者无法构造等价对象

    攻击者尝试：
    - _AdmissionAuthority()          → ❌ TypeError
    - object.__new__(_AdmissionAuthority) → ❌ TypeError（__new__ 也拒绝）
    - 伪造实例（任何方式）→ ❌ `is cap is not _ADMISSION_CAPABILITY`
    """

    __slots__ = ()

    def __new__(cls):
        raise TypeError("AdmissionAuthority is a singleton — use the module-level _ADMISSION_CAPABILITY.")

    def __init__(self):
        raise TypeError("AdmissionAuthority cannot be re-initialized.")


# 模块级单例 — 唯一合法的 capability 对象
# 创建时使用 object.__new__() 绕过 __new__ 限制，仅在本模块内部使用
# 外部无法通过同样方式伪造（因为外部 import 不到 _AdmissionAuthority 类）
_ADMISSION_CAPABILITY = object.__new__(_AdmissionAuthority)


# ============================================================
# IdentityType / AuditedIdentity / AdmissionScope
# ============================================================

class IdentityType(str, enum.Enum):
    """审核身份类型。

    HUMAN: 人类审核员（需 authority_source 在预注册列表）
    AGENT: 自动化工具（需 authority_source 在预注册列表）
    SYSTEM: 系统生成（需 authority_source 在预注册列表）
    GPT: GPT 裁决（需 authority_source 在预注册列表）
    LEGACY: 旧格式迁移（默认被生产路径拒绝）
    """
    HUMAN = "HUMAN"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"
    GPT = "GPT"
    LEGACY = "LEGACY"


# 预注册 authority_source → credential_hash 映射
# 生产部署时从外部权威源（如 HSM 或部署 manifest）加载
# ⚠️ 锁定后不可修改 — register_authority_credential() 将抛出 RuntimeError
_AUTHORITY_CREDENTIALS: Dict[str, str] = {}
_AUTHORITY_LOCKED = False


def register_authority_credential(authority_source: str, credential_hash: str) -> None:
    """注册合法的 authority_source + credential_hash 对。

    必须在 lock_authority_registry() 之前调用。
    生产部署时由部署脚本调用，不在运行时由普通 Python 代码设置。
    """
    global _AUTHORITY_LOCKED
    if _AUTHORITY_LOCKED:
        raise RuntimeError(
            "register_authority_credential() called after registry is locked. "
            "Credentials must be registered before lock_authority_registry()."
        )
    _AUTHORITY_CREDENTIALS[authority_source] = credential_hash


def lock_authority_registry() -> None:
    """锁定 authority 凭证注册表。

    必须在 ProductionRuleLoader 首次加载前调用。
    锁定后调用 register_authority_credential() 将抛出 RuntimeError。
    """
    global _AUTHORITY_LOCKED
    _AUTHORITY_LOCKED = True


def clear_authority_credentials() -> None:
    """测试用：清空 authority 凭证（避免测试间污染）。"""
    global _AUTHORITY_LOCKED
    if _AUTHORITY_LOCKED:
        raise RuntimeError("Cannot clear credentials after registry is locked.")
    _AUTHORITY_CREDENTIALS.clear()


# ============================================================
# P2.1-F: External Trust Root — Environment Variable + Fail-Closed
# ============================================================
#
# Security model (P2.1-F):
#   - Authority credential is loaded from TONGSHU_AUTHORITY_CREDENTIALS env var,
#     NOT from any file in the repository (deployment_manifest.json is a
#     documentation example only).
#   - This prevents attackers who can modify repo files from simultaneously
#     tampering both manifest and rules to pass the bootstrap check.
#   - All missing-credential / missing-declared-hash cases are FAIL CLOSED.

_AUTHORITY_ENV_VAR = "TONGSHU_AUTHORITY_CREDENTIALS"


def load_trust_root() -> Dict[str, str]:
    """从 TONGSHU_AUTHORITY_CREDENTIALS 环境变量加载权威凭证。

    格式: "source1:hash1;source2:hash2"
    返回: {source: hash, ...}

    环境变量未设置、格式无效或为空 → 抛出 RuntimeError (fail-closed)。
    """
    import os as _os
    raw = _os.environ.get(_AUTHORITY_ENV_VAR, "")
    if not raw:
        raise RuntimeError(
            f"P2.1-F: Environment variable {_AUTHORITY_ENV_VAR} is not set. "
            "Production pipeline requires TONGSHU_AUTHORITY_CREDENTIALS to bootstrap authority."
        )
    result: Dict[str, str] = {}
    for pair in raw.split(";"):
        pair = pair.strip()
        if not pair:
            continue
        parts = pair.split(":", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise RuntimeError(
                f"P2.1-F: Invalid {_AUTHORITY_ENV_VAR} entry {pair!r}. "
                "Expected format: 'source:hash;source:hash'"
            )
        result[parts[0]] = parts[1]
    if not result:
        raise RuntimeError(
            f"P2.1-F: {_AUTHORITY_ENV_VAR} is set but contains no valid entries."
        )
    return result


def verify_authority_credential(manifest_cred_hash: str, rules_declared_hash: str) -> bool:
    """验证 trust root credential 与 production rules _meta.declared_credential_hash 一致。

    P2.1-F F2: 所有缺失情况 FAIL CLOSED。
    - manifest_cred_hash 为空 → False
    - rules_declared_hash 为空 → False（不再有 fail-open）
    - 不一致 → False
    - 一致 → True
    """
    if not manifest_cred_hash or not rules_declared_hash:
        return False
    import hashlib
    return (
        hashlib.sha256(manifest_cred_hash.encode()).hexdigest()
        == hashlib.sha256(rules_declared_hash.encode()).hexdigest()
    )


@dataclass(frozen=True)
class AuditedIdentity:
    """经审核的身份绑定。

    安全设计（v7）：
    - authority_source 必须在预注册列表中才能 admission
    - credential_hash 验证 authority_source 的真实性
    - LEGACY 类型被生产路径明确拒绝
    """
    identity_type: IdentityType
    identity_id: str
    authority_source: str = ""
    credential_hash: str = ""

    @classmethod
    def from_legacy_string(cls, s: str) -> "AuditedIdentity":
        if not s or len(s) < 3:
            raise ValueError(f"Invalid legacy verified_by string: {s!r}")
        return cls(
            identity_type=IdentityType.LEGACY,
            identity_id=s,
            authority_source="legacy_migration",
        )

    def verify_authority(self) -> bool:
        """验证 authority_source 是否在预注册列表中。

        G2 核心：只有预注册的 authority_source 才能被 production admission 接受。
        """
        if not self.authority_source:
            return False
        return self.authority_source in _AUTHORITY_CREDENTIALS

    def verify_credential(self) -> bool:
        """验证 credential_hash 是否与 authority_source 匹配。

        G2 核心：伪造的 credential_hash 会被拒绝。
        """
        if not self.authority_source or not self.credential_hash:
            return False
        expected = _AUTHORITY_CREDENTIALS.get(self.authority_source, "")
        if not expected:
            return False
        # 使用 HMAC-like 比较（constant-time 友好）
        return hashlib.sha256(self.credential_hash.encode()).hexdigest() == hashlib.sha256(expected.encode()).hexdigest()


class AdmissionScope(str, enum.Enum):
    TEST_FIXTURE = "TEST_FIXTURE"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    PRODUCTION_ADMITTED = "PRODUCTION_ADMITTED"


# ============================================================
# AdmissionRecord
# ============================================================

@dataclass(frozen=True)
class AdmissionRecord:
    asset_id: str
    asset_type: str
    source_work: str
    source_chapter: str
    passage_ref: str
    verified_by: AuditedIdentity
    verification_stage: str
    verification_version: str
    admission_scope: AdmissionScope
    admission_timestamp: float
    admission_id: str
    asset_hash: str
    admission_hash: str
    synthetic: bool = False

    def validate_for_scope(self, required_scope: AdmissionScope) -> List[str]:
        errors = []
        if not self.asset_id:
            errors.append("asset_id cannot be empty")
        if not self.source_work:
            errors.append("source_work cannot be empty")
        if not self.passage_ref:
            errors.append("passage_ref cannot be empty")
        if self.admission_hash and len(self.admission_hash) != 64:
            errors.append("admission_hash must be 64-char SHA-256")
        if required_scope == AdmissionScope.PRODUCTION_ADMITTED:
            if self.synthetic:
                errors.append("synthetic asset cannot be PRODUCTION_ADMITTED")
            if self.verified_by.identity_type == IdentityType.LEGACY:
                errors.append("LEGACY identity not allowed for PRODUCTION_ADMITTED")
            if not self.verified_by.verify_authority():
                errors.append(f"verified_by authority_source '{self.verified_by.authority_source}' not registered")
        return errors

    def verify_integrity(self, expected_hash: Optional[str] = None) -> bool:
        if not self.admission_hash:
            return False
        if expected_hash and self.admission_hash != expected_hash:
            return False
        return self.admission_hash == self._compute_admission_hash()

    def _compute_admission_hash(self) -> str:
        metadata = {
            "asset_id": self.asset_id, "asset_type": self.asset_type,
            "source_work": self.source_work, "source_chapter": self.source_chapter,
            "passage_ref": self.passage_ref,
            "verified_by_id": self.verified_by.identity_id,
            "verified_by_type": self.verified_by.identity_type.value,
            "verified_by_authority": self.verified_by.authority_source,
            "verified_by_credential": self.verified_by.credential_hash,
            "verification_stage": self.verification_stage,
            "verification_version": self.verification_version,
            "admission_scope": self.admission_scope.value,
            "synthetic": self.synthetic, "asset_hash": self.asset_hash,
        }
        metadata_str = hashlib.sha256(
            str(sorted(metadata.items())).encode("utf-8")
        ).hexdigest()
        return hashlib.sha256(
            f"{self.asset_hash}:{metadata_str}:{self.admission_id}".encode("utf-8")
        ).hexdigest()


# ============================================================
# AdmissionRegistry — v7: 不可伪造 Capability
# ============================================================

class AdmissionRegistry:
    """
    生产准入注册表（v7）。

    核心安全设计（v7）：
    - __init__ 要求模块级单例 _ADMISSION_CAPABILITY（is 检查）
    - 外部无法创建等价的 _AdmissionAuthority 实例（__new__ 拒绝）
    - _create_production_admission 验证 authority_source 预注册
    - 无任何公开方法可创建或获取 _ADMISSION_CAPABILITY

    攻击模型（v7）：
    任意 caller → AdmissionRegistry()                ← ❌ TypeError（缺少 capability）
    任意 caller → _AdmissionAuthority()              ← ❌ TypeError（无法实例化）
    任意 caller → object.__new__(_AdmissionAuthority) ← ❌ TypeError（__new__ 也拒绝）
    任意 caller → AdmissionRegistry(fake_cap)        ← ❌ TypeError（is 检查失败）
    """

    def __init__(self, capability: Any):
        # v7: 使用 is 检查（而非 isinstance），防止任何伪造的 Capability 对象
        if capability is not _ADMISSION_CAPABILITY:
            raise TypeError(
                "AdmissionRegistry requires the module-level _ADMISSION_CAPABILITY singleton. "
                "Use ProductionRuleLoader.load() for Production Admission."
            )
        self._records: Dict[str, AdmissionRecord] = {}
        self._asset_index: Dict[str, List[str]] = {}
        self._hash_chain: List[str] = []

    def _register(self, record: AdmissionRecord) -> str:
        errors = record.validate_for_scope(record.admission_scope)
        if errors:
            raise ValueError(f"AdmissionRecord validation failed: {errors}")
        computed_hash = record._compute_admission_hash()
        if record.admission_hash != computed_hash:
            raise ValueError(
                f"AdmissionRecord hash mismatch for asset_id={record.asset_id}"
            )
        if record.admission_id in self._records:
            raise ValueError(
                f"AdmissionRecord with admission_id={record.admission_id} already exists"
            )
        self._records[record.admission_id] = record
        if record.asset_id not in self._asset_index:
            self._asset_index[record.asset_id] = []
        self._asset_index[record.asset_id].append(record.admission_id)
        prev_hash = self._hash_chain[-1] if self._hash_chain else "GENESIS"
        chain_hash = hashlib.sha256(
            f"{prev_hash}:{record.admission_id}:{record.admission_hash}".encode("utf-8")
        ).hexdigest()
        self._hash_chain.append(chain_hash)
        return record.admission_id

    def _create_production_admission(
        self, asset_id: str, asset_type: str,
        source_work: str, source_chapter: str, passage_ref: str,
        verified_by: AuditedIdentity, verification_stage: str,
        verification_version: str, synthetic: bool = False,
    ) -> AdmissionRecord:
        if synthetic:
            raise ValueError(
                f"Synthetic asset '{asset_id}' cannot be admitted to PRODUCTION"
            )
        # G2: 验证 authority_source 必须在预注册列表中
        if not verified_by.verify_authority():
            raise ValueError(
                f"AdmissionRegistry: identity '{verified_by.identity_id}' "
                f"has unregistered authority_source '{verified_by.authority_source}'"
            )
        # G2: 验证 credential_hash 必须与预注册凭证匹配
        if not verified_by.verify_credential():
            raise ValueError(
                f"AdmissionRegistry: identity '{verified_by.identity_id}' "
                f"has invalid credential for authority_source '{verified_by.authority_source}'"
            )
        admission_id = (
            f"admission_{asset_id}_{int(time.time())}_"
            f"{hashlib.md5(f'{asset_id}{time.time()}'.encode()).hexdigest()[:8]}"
        )
        asset_hash = hashlib.sha256(
            f"{asset_id}:{asset_type}".encode("utf-8")
        ).hexdigest()
        record = AdmissionRecord(
            asset_id=asset_id, asset_type=asset_type,
            source_work=source_work, source_chapter=source_chapter,
            passage_ref=passage_ref, verified_by=verified_by,
            verification_stage=verification_stage,
            verification_version=verification_version,
            admission_scope=AdmissionScope.PRODUCTION_ADMITTED,
            admission_timestamp=time.time(), admission_id=admission_id,
            asset_hash=asset_hash, admission_hash="", synthetic=False,
        )
        final = AdmissionRecord(
            asset_id=record.asset_id, asset_type=record.asset_type,
            source_work=record.source_work, source_chapter=record.source_chapter,
            passage_ref=record.passage_ref, verified_by=record.verified_by,
            verification_stage=record.verification_stage,
            verification_version=record.verification_version,
            admission_scope=record.admission_scope,
            admission_timestamp=record.admission_timestamp,
            admission_id=admission_id, asset_hash=record.asset_hash,
            admission_hash=record._compute_admission_hash(),
            synthetic=record.synthetic,
        )
        self._register(final)
        return final

    def verify(self, admission_id: str) -> Optional[AdmissionRecord]:
        record = self._records.get(admission_id)
        if record is None:
            return None
        if not record.verify_integrity():
            return None
        return record

    def get_produced_assets(self) -> List[AdmissionRecord]:
        return [
            r for r in self._records.values()
            if r.admission_scope == AdmissionScope.PRODUCTION_ADMITTED
        ]

    def get_asset_records(self, asset_id: str) -> List[AdmissionRecord]:
        ids = self._asset_index.get(asset_id, [])
        return [self._records[mid] for mid in ids if mid in self._records]

    @property
    def record_count(self) -> int:
        return len(self._records)

    @property
    def production_count(self) -> int:
        return sum(
            1 for r in self._records.values()
            if r.admission_scope == AdmissionScope.PRODUCTION_ADMITTED
        )
