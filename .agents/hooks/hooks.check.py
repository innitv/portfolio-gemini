# -*- coding: utf-8 -*-
"""
Проверка защитников: каждый обязан и сработать, и НЕ сработать где не надо.

Случаи подобраны парами — опасное действие и похожее безобидное. Без второй
половины защитник легко оказывается слишком широким: первая версия защитника
секретов блокировала команду, где имя файла лежало внутри тестовых данных.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SECRET = ".env" + ".portfolio-deploy"  # склейка, чтобы не ловить самого себя

CASES = [
    # (хук, ввод, ожидаемое решение, что проверяем)
    ("guard-generated.py",
     {"toolCall": {"name": "edit_file", "args": {"Path": "src/views/portfolio-images.generated.ts"}}},
     "deny", "правка сгенерированного манифеста"),
    ("guard-generated.py",
     {"toolCall": {"name": "edit_file", "args": {"Path": "src/views/portfolio.data.ts"}}},
     "allow", "правка обычных данных"),
    ("guard-secrets.py",
     {"toolCall": {"name": "read_file", "args": {"Path": f"C:/Project/siteportfolio/{SECRET}"}}},
     "deny", "чтение файла с паролем"),
    ("guard-secrets.py",
     {"toolCall": {"name": "read_file", "args": {"Path": f"{SECRET}.example"}}},
     "allow", "чтение шаблона без пароля"),
    ("guard-secrets.py",
     {"toolCall": {"name": "run_command", "args": {"CommandLine": f"cat {SECRET}"}}},
     "deny", "вывод файла целиком"),
    ("guard-secrets.py",
     {"toolCall": {"name": "run_command", "args": {"CommandLine": f"grep PASSWORD {SECRET}"}}},
     "deny", "вывод одной строки с паролем"),
    ("guard-secrets.py",
     {"toolCall": {"name": "run_command", "args": {"CommandLine": f"ls -la {SECRET}"}}},
     "allow", "просмотр размера файла"),
    ("guard-secrets.py",
     {"toolCall": {"name": "run_command", "args": {"CommandLine": f"echo 'cat {SECRET}' > note.txt"}}},
     "allow", "имя файла внутри строки, а не вызова"),
    ("guard-secrets.py",
     {"toolCall": {"name": "run_command", "args": {"CommandLine": "python tools/upload-portfolio-ftp.py"}}},
     "allow", "скрипт, который читает доступы сам"),
]

failures = 0
for hook, payload, expected, title in CASES:
    result = subprocess.run(
        [sys.executable, f".agents/hooks/{hook}"],
        capture_output=True, cwd=ROOT, input=json.dumps(payload), text=True, timeout=30,
    )
    try:
        decision = json.loads(result.stdout).get("decision")
    except (json.JSONDecodeError, ValueError):
        decision = f"invalid({result.returncode})"

    ok = result.returncode == 0 and decision == expected
    mark = "ok " if ok else "FAIL"
    if not ok:
        failures += 1
    print(f"[{mark}] {title:42} decision={decision}, zhdali={expected}")

print()
print("proval:" if failures else "vse sluchai proshli:", failures or len(CASES))
sys.exit(1 if failures else 0)
