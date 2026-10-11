# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
import json, os
OUT = r'D:\shuntian-ziping-p0\p0_v2\case_audit'
for book in ['DTS','PZZQ','QTBJ','YHZP','SFTK','SMTH']:
    cp = os.path.join(OUT, book + '_clean.jsonl')
    dp = os.path.join(OUT, '_' + book + '_deleted.jsonl')
    kept = sum(1 for _ in open(cp, encoding='utf-8'))
    dele = sum(1 for _ in open(dp, encoding='utf-8')) if os.path.exists(dp) else 0
    print(book + ': kept=' + str(kept) + ' deleted=' + str(dele))
    if dele:
        for l in open(dp, encoding='utf-8'):
            r = json.loads(l)
            cid = r.get('case_id','')
            bz = r.get('bazi','')
            reason = r.get('pass_reason', r.get('verdict_reason',''))[:80]
            print('  DEL ' + cid + ' | ' + bz + ' | ' + reason)
