"""V2.2.2 FINAL 错误体系。

所有异常继承 ShuntianError；关键失败必须 FAIL_CLOSED（§72）。
"""


class ShuntianError(Exception):
    """基类。"""


class SchemaValidationError(ShuntianError):
    """Schema 不合法或实例校验失败。"""


class ContractError(ShuntianError):
    """Contract 不匹配或输入输出越界。"""


class CanonicalGateError(ShuntianError):
    """Canonical Gate 失败。携带 gate_id。"""

    def __init__(self, gate_id: str, message: str):
        self.gate_id = gate_id
        super().__init__(f"[{gate_id}] {message}")


class BoundaryViolation(ShuntianError):
    """Static Import Boundary 或 Runtime Input Boundary 违规。"""


class ForbiddenSymbolError(ShuntianError):
    """扫描到禁用符号（score/confidence/LLM/sxtwl 等）。"""


class GoldenPermissionError(ShuntianError):
    """Golden 权限违规（Agent 试图创建/修改/删除 Golden）。"""


class RegistryError(ShuntianError):
    """Registry 读写违规（无 Source 的 Rule、无 Evidence 的 Judgment 等）。"""


class StateModelError(ShuntianError):
    """状态模型违规（如把 RULE_NOT_APPLICABLE 转成 UNKNOWN 或否定）。"""
