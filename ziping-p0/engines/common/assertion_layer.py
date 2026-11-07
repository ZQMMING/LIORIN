# -*- coding: utf-8 -*-
"""PATCH-102 Assertion Layer 经典断言层
State=机器事实, Assertion=经典判断, Explanation=最终表达
铁律: Assertion只读State+Relation, 禁止Assertion→State
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def assertion_schema(assertion_id, classic_source, evidence_id, namespace,
                     required_state, relation_requirement, assertion_text, assertion_type):
    return {
        "assertion_id": assertion_id,
        "classic_source": classic_source,
        "evidence_id": evidence_id,
        "namespace": namespace,
        "required_state": required_state,
        "relation_requirement": relation_requirement,
        "assertion_text": assertion_text,
        "assertion_type": assertion_type,
        "status": "CANDIDATE",
        "guard": "Assertion只读State+Relation, 不生产State"
    }


def assertion_matcher(state_pack, assertion):
    """State+Relation+Condition→Assertion Output, 禁止反写State"""
    rs = assertion["required_state"]
    # 条件匹配(示例: 财格+印透)
    if state_pack.get("pattern") == "财格" and state_pack.get("resource_visible"):
        return {"assertion_id": assertion["assertion_id"],
                "output": assertion["assertion_text"],
                "matched": True,
                "guard": "不反写State"}
    return {"assertion_id": assertion["assertion_id"], "matched": False}


if __name__ == '__main__':
    a = assertion_schema(
        "ASSERT-001", "PZZQ", "PZZQ-007-004", "PZZQ.pattern",
        {"pattern": "财格", "resource_visible": True}, "印相位置安帖两不相克",
        "财格佩印，位置安帖，两不相克，格成", "SUCCESS")
    print("=== Assertion Schema ===")
    print(a["assertion_id"], a["classic_source"], a["assertion_type"])
    print("\n=== Matcher ===")
    print(assertion_matcher({"pattern": "财格", "resource_visible": True}, a))
