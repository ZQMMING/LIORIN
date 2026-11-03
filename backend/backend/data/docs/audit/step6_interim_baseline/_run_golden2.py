"""Run golden suite with extended timeout (500s)."""
import subprocess, sys, os
os.chdir("D:/today/backend")
env = os.environ.copy()
env["PYTHONPATH"] = "src"
env["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"
r = subprocess.run([sys.executable, "-m", "tongshu.golden"],
                   capture_output=True, text=True, env=env, timeout=500)
with open("docs/audit/step6_interim_baseline/golden-interim.log", "w", encoding="utf-8") as f:
    f.write(r.stdout)
    if r.stderr:
        f.write("\n--- STDERR ---\n")
        f.write(r.stderr)
print(r.stdout[-2000:])
if r.stderr:
    print("STDERR:", r.stderr[-500:])
print(f"exit code: {r.returncode}")
