#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三族合并规则边界测试

b3事件的制度化回应：断言floor/promote/demote不越界
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from spec.merge_rules import MERGE_SPEC, CONFIRMED, MID, REJECT


def test_no_out_of_range():
    """所有档位都在合法枚举内"""
    valid = {CONFIRMED, MID, REJECT}
    for spec_name, spec in MERGE_SPEC.items():
        # 检查promote档位
        for _, conf in spec["promote"]:
            assert conf in valid, f"{spec_name} promote档位越界: {conf}"
        # 检查conditional档位
        for _, conf in spec["conditional"]:
            assert conf in valid, f"{spec_name} conditional档位越界: {conf}"
        # 检查demote档位
        for _, conf in spec["demote"]:
            assert conf in valid, f"{spec_name} demote档位越界: {conf}"
        # 检查floor
        assert spec["floor"] in valid, f"{spec_name} floor越界: {spec['floor']}"
    print("✅ 所有档位都在合法枚举内")


def test_floor_not_below_reject():
    """floor不能低于REJECT"""
    for spec_name, spec in MERGE_SPEC.items():
        # REJECT是最低档，floor不能比它还低
        assert spec["floor"] != REJECT, f"{spec_name} floor不能是REJECT（否则所有用例都REJECT）"
    print("✅ floor不低于MID，不会全REJECT")


def test_hard_gates_are_reject():
    """所有hard_gates的结果都是REJECT，且不受floor保护"""
    for spec_name, spec in MERGE_SPEC.items():
        for _, conf in spec["hard_gates"]:
            assert conf == REJECT, f"{spec_name} hard_gate必须是REJECT"
    print("✅ 所有hard_gates都是REJECT，且不受floor保护")


def test_化气_conditional_order():
    """化气型conditional顺序：先判b5=False&b3=False（REJECT），再判b5=False&b3=True（MID）"""
    spec = MERGE_SPEC["化气型"]
    conds = [c[0] for c in spec["conditional"]]
    # 应该先REJECT再MID
    assert "b5=False & b3=False" in conds[0], "化气型conditional第一条应该是b5=False&b3=False→REJECT"
    assert "b5=False & b3=True" in conds[1], "化气型conditional第二条应该是b5=False&b3=True→MID"
    print("✅ 化气型conditional顺序正确（先REJECT再MID）")


if __name__ == "__main__":
    test_no_out_of_range()
    test_floor_not_below_reject()
    test_hard_gates_are_reject()
    test_化气_conditional_order()
    print("\n🎉 全部通过")
