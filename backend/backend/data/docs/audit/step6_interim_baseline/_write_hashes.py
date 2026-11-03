lines = [
    'e6d302808d82f7c981dd0aaeac8e1dd642eba717636d24aae1f677efcda92d85 *GIT_STATE.txt',
    '3fcd80e1594a75db146957e63b94b08496cb954fa805bd0c367148a90d589a5d *pytest-interim.log',
    '80983acd030f6aa8bdaba616c0ff452568e7cf62f1b320c712cc94fe6c013a47 *DB_SNAPSHOT_INTERIM.md',
    'af7ec67984e1e9c0ee5ff99eb7ea62a169f816702c5b3929e61fa5a0c6537fee *GOLDEN_RECHECK.md',
    'c617d6445e0809a6e69b60259b0bbf5b095125e5cb60668e0404cbee3a0706ca *golden-interim.log',
    '63af1b8f57f91b1060c1aedb5ce9b6ee4d8cf73c025af648d725ad9030112609 *GATE_INTERIM.txt',
    '530edc231e31badd2d65d27c4aa80bbda070e4505ef07b7ed5095425b49c3f51 *FREEZE_INTERIM.txt',
    'd9b47f57776715057fd9aab9024004bc3fbc0952dde7d60c4e8768f27e41d52f *../../../../docs/audit/step0_baseline/GOLDEN_BASELINE.md',
]
with open('docs/audit/step6_interim_baseline/INTERIM_HASHES.sha256', 'w', newline='\n') as f:
    f.write('\n'.join(lines) + '\n')
print('OK')
