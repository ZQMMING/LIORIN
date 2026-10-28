# -*- coding: utf-8 -*-
"""PATCH-081 用神Relation Contract
铁律: 不生产新用神(026已冻结三用); 只描述三用关系, 不人为排序
取消PRIMARY_DOMAIN(隐藏优先级); 消费场景决定用哪个, 非谁高级
"""
import io, sys

USE_RELATION_ENUM = ["COEXIST", "SUPPORT", "OPPOSE", "CONDITION_DEPENDENT", "INDEPENDENT"]


def use_relation(source, target, relation, evidence):
    """
    source/target: (namespace, state)
    relation: 五型之一
    """
    if relation not in USE_RELATION_ENUM:
        return {"state": "use_relation", "status": "INVALID_RELATION"}
    return {
        "relation_state": relation,
        "source": {"namespace": source[0], "state": source[1]},
        "target": {"namespace": target[0], "state": target[1]},
        "evidence_chain": evidence,
        "judgment": "ABSTAIN",
        "guard": "不改use_god_state/不产strength/不覆盖用神"
    }


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== PATCH-081 用神Relation ===")
    # GC-001: PZZQ用财 / SFTK药用印 / QTBJ调候用癸
    print("财↔印(格局↔病药):", use_relation(
        ("PZZQ.use_god", "财"), ("SFTK.qu_yong", "印"),
        "CONDITION_DEPENDENT", ["PZZQ-005-007", "SFTK-008-001"])["relation_state"])
    print("癸↔印(调候↔病药):", use_relation(
        ("QTBJ.climate_use", "癸"), ("SFTK.qu_yong", "印"),
        "SUPPORT", ["QTBJ-022-001", "SFTK-008-001"])["relation_state"])
    print("财↔癸(格局↔调候):", use_relation(
        ("PZZQ.use_god", "财"), ("QTBJ.climate_use", "癸"),
        "INDEPENDENT", ["PZZQ-005-007", "QTBJ-022-001"])["relation_state"])
    print("\n禁: 格局用>调候用/调候用>扶抑用 的人为排序")
