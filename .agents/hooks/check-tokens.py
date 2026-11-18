# -*- coding: utf-8 -*-
"""
После правки стилей сразу гоняется сторож значений.

`yarn tokens:check` ловит цвет, время и кривую, записанные по месту, кратность
отступов и границы `@media` вне шкалы 640/900/1200. Проверка занимает доли
секунды, но её вспоминают в конце работы — когда таких правок накопилось
десяток и непонятно, какая нарушила правило.

Хук печатает результат в stderr, а в stdout отдаёт `{}` по контракту
PostToolUse в Antigravity: код возврата 0, работа не прерывается.
"""
import json
import subprocess
import sys
from pathlib import Path

WATCHED = ("src/styles/",)
ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print("{}")
        return 0

    tool_call = payload.get("toolCall") or {}
    args = tool_call.get("args") or {}
    path = str(
        args.get("Path")
        or args.get("TargetFile")
        or args.get("file_path")
        or ""
    ).replace("\\", "/")

    if not path.endswith(".css") or not any(part in path for part in WATCHED):
        print("{}")
        return 0

    try:
        result = subprocess.run(
            ["node", "tests/tokens.check.mjs"],
            capture_output=True,
            cwd=ROOT,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(f"tokens:check не запустился: {error}", file=sys.stderr)
        print("{}")
        return 0

    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        print(f"tokens:check — {output.splitlines()[-1] if output else 'pass'}", file=sys.stderr)
    else:
        print(
            "🔴 tokens:check упал после правки стилей:\n"
            f"{output}\n"
            "Значение написано по месту вместо роли — или заведена точка перелома "
            "вне шкалы 640/900/1200.",
            file=sys.stderr,
        )

    print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
