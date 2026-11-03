"""Read-only dual-DB snapshot for STEP 6 interim baseline."""
import psycopg2

def snapshot(dsn, name):
    conn = psycopg2.connect(dsn)
    conn.set_session(readonly=True)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
    tcount = cur.fetchone()[0]
    cur.execute("SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname")
    rows = cur.fetchall()
    total = sum(r[1] for r in rows)
    populated = sum(1 for r in rows if r[1] > 0)
    print(f"=== {name} ===")
    print(f"DSN: {dsn}")
    print(f"TABLE_COUNT={tcount}")
    print(f"TOTAL_ROWS={total}")
    print(f"POPULATED={populated}/{tcount}")
    for rel in ["rules","evidence","mappings","books","passages",
                "classical_concepts","principles","rule_versions",
                "mapping_versions","migration_versions","schema_versions"]:
        try:
            cur.execute(f"SELECT count(*) FROM {rel}")
            print(f"  {rel}={cur.fetchone()[0]}")
        except Exception as e:
            print(f"  {rel}=N/A ({e})")
    # rules by status
    try:
        cur.execute("SELECT status, count(*) FROM rules GROUP BY status ORDER BY status")
        for st, cnt in cur.fetchall():
            print(f"  rules[{st}]={cnt}")
    except Exception:
        pass
    cur.close()
    conn.close()
    print()

snapshot("postgresql://postgres:postgres@127.0.0.1:5432/otcg", "otcg (runtime)")
snapshot("postgresql://postgres:postgres@127.0.0.1:5432/shuntian_kb", "shuntian_kb (knowledge)")
