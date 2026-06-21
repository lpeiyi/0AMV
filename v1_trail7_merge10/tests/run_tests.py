"""0AMVMonitor 统一测试运行器"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PY = sys.executable

TESTS = [
    ("综合单元测试 (62项)", "tests_comprehensive.py"),
    ("Settings 集成测试 (25项)", "tests_integration.py"),
]

all_ok = True
for label, script in TESTS:
    path = os.path.join(HERE, script)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    ret = subprocess.run([PY, path], cwd=PROJ)
    if ret.returncode != 0:
        all_ok = False

print(f"\n{'='*60}")
print(f"  {'全部测试通过' if all_ok else '部分测试失败'}")
print(f"{'='*60}")
sys.exit(0 if all_ok else 1)
