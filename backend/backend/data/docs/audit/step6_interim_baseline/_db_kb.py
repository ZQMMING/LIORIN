"""Read-only shuntian_kb snapshot (autocommit to avoid txn abort on missing tables)."""
import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres@127.0.0.1:5432/shuntian_kb")
conn.set_session(readonly=True, autocommit=True)
cur = conn.cursor()

cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
print("TABLE_COUNT=" + str(cur.fetchone()[0]))

cur.execute("SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname")
rows = cur.fetchall()
print("TOTAL_ROWS=" + str(sum(r[1] for r in rows)))
print("POPULATED=" + str(sum(1 for r in rows if r[1] > 0)))

for rel in ["rules", "evidence", "passages", "principles", "books", "classical_concepts"]:
    try:
        cur.execute(f"SELECT count(*) FROM {rel}")
        print(f"  {rel}=" + str(cur.fetchone()[0]))
    except Exception:
        print(f"  {rel}=N/A")

cur.close()
conn.close()
