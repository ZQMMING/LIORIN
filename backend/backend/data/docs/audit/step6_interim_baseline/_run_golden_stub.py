"""Run golden suite forcing StubLLMClient (no API key, .env blocked)."""
import subprocess, sys, os

os.chdir("D:/today/backend")
env = os.environ.copy()
env["PYTHONPATH"] = "src"
env["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"
env["PYTHONUNBUFFERED"] = "1"
# Block .env loading and clear any API keys → forces StubLLMClient
env["TONGSHU_ENV_FILE"] = "Z:/nonexistent_no_env.env"
env.pop("TONGSHU_LLM_API_KEY", None)
env.pop("DEEPSEEK_API_KEY", None)

proc = subprocess.run(
    [sys.executable, "-m", "tongshu.golden"],
    capture_output=True, text=True, env=env, timeout=300
)

with open("docs/audit/step6_interim_baseline/golden-interim.log", "w", encoding="utf-8") as f:
    f.write(proc.stdout)
    if proc.stderr:
        f.write("\n--- STDERR ---\n")
        f.write(proc.stderr)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr[-500:])
print(f"exit code: {proc.returncode}")
