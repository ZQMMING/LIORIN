"""Run golden suite with streaming output and per-case timeout."""
import subprocess, sys, os
os.chdir("D:/today/backend")
env = os.environ.copy()
env["PYTHONPATH"] = "src"
env["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"
env["PYTHONUNBUFFERED"] = "1"

proc = subprocess.Popen(
    [sys.executable, "-m", "tongshu.golden"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, env=env, encoding="utf-8"
)

lines = []
try:
    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            print(line.rstrip())
            lines.append(line)
except KeyboardInterrupt:
    proc.kill()

with open("docs/audit/step6_interim_baseline/golden-interim.log", "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"\nexit code: {proc.returncode}")
