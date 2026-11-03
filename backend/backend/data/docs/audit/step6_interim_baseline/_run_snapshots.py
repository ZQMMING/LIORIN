"""Run pytest and golden suite, save logs, print DB snapshot."""
import subprocess, sys, os

os.chdir("D:/today/backend")
env = os.environ.copy()
env["PYTHONPATH"] = "src"

# 1. pytest
print("=== PYTEST ===")
r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"],
                   capture_output=True, text=True, env=env, timeout=300)
with open("docs/audit/step6_interim_baseline/pytest-interim.log", "w", encoding="utf-8") as f:
    f.write(r.stdout)
    if r.stderr:
        f.write("\n--- STDERR ---\n")
        f.write(r.stderr)
print(r.stdout[-500:] if len(r.stdout) > 500 else r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[-200:])
print(f"pytest exit code: {r.returncode}")

# 2. golden
print("\n=== GOLDEN ===")
env["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"
r2 = subprocess.run([sys.executable, "-m", "tongshu.golden"],
                    capture_output=True, text=True, env=env, timeout=120)
with open("docs/audit/step6_interim_baseline/golden-interim.log", "w", encoding="utf-8") as f:
    f.write(r2.stdout)
    if r2.stderr:
        f.write("\n--- STDERR ---\n")
        f.write(r2.stderr)
print(r2.stdout)
if r2.stderr:
    print("STDERR:", r2.stderr[-200:])
print(f"golden exit code: {r2.returncode}")

# 3. DB snapshot
print("\n=== DB SNAPSHOT ===")
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
    print(f"--- {name} ---")
    print(f"TABLE_COUNT={tcount} TOTAL_ROWS={total} POPULATED={populated}/{tcount}")
    for rel in ["rules","evidence","mappings","books","passages",
                "classical_concepts","principles","rule_versions",
                "mapping_versions","migration_versions","schema_versions"]:
        try:
            cur.execute(f"SELECT count(*) FROM {rel}")
            print(f"  {rel}={cur.fetchone()[0]}")
        except Exception as e:
            print(f"  {rel}=N/A")
    try:
        cur.execute("SELECT status, count(*) FROM rules GROUP BY status ORDER BY status")
        for st, cnt in cur.fetchall():
            print(f"  rules[{st}]={cnt}")
    except Exception:
        pass
    cur.close()
    conn.close()

snapshot("postgresql://postgres:postgres@127.0.0.1:5432/otcg", "otcg")
snapshot("postgresql://postgres:postgres@127.0.0.1:5432/shuntian_kb", "shuntian_kb")
