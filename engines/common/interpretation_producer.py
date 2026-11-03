# -*- coding: utf-8 -*-
"""PATCH-159 Interpretation Producer
消费158 Judgment -> 现代语言释义. 不改Judgment, 不新增判断.
PENDING不产确定释义; LLM暂不接."""


def produce_interpretation(judgment):
    if judgment.get('status') == 'PENDING_REVIEW':
        return {'interpretation_id': None, 'judgment_id': judgment.get('judgment_id'),
                'plain_text': None, 'status': 'PENDING_REVIEW',
                'note': '待判, 不产确定性释义'}
    direction = judgment.get('direction')
    subj = judgment.get('subject')
    if direction == 'SUPPORTED':
        text = f"{subj}格局候选方向：required条件已满足、已知blocked未命中，记为SUPPORTED。此为候选方向记录，非成格/吉凶结论。"
    elif direction == 'NOT_SUPPORTED':
        text = f"{subj}格局候选方向：存在required未满足或已知blocked命中，记为NOT_SUPPORTED。此为候选方向记录，非成格/吉凶结论。"
    else:
        return {'interpretation_id': None, 'judgment_id': judgment.get('judgment_id'),
                'plain_text': None, 'status': 'UNKNOWN_JUDGMENT_DIRECTION',
                'note': '未知Judgment方向, 不产释义'}
    return {
        'interpretation_id': f"INT-{judgment.get('judgment_id','?')}",
        'judgment_id': judgment.get('judgment_id'),
        'plain_text': text,
        'language': 'zh-CN',
        'based_on': judgment.get('assertion_ids', []),
        'source_evidence': judgment.get('evidence', []),
        'authorization': judgment.get('authorization', 'RECORDED'),
        'status': 'RECORDED',
        'note': '仅表达, 不新增判断',
    }
