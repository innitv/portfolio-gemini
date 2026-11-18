# -*- coding: utf-8 -*-
"""
Защитник: сгенерированные файлы не правятся руками.

🔴 Зачем хук, если правило уже написано в GEMINI.md. Потому что правило читают
один раз, а нарушают в момент, когда «надо быстро дописать один ключ». Так в
манифест кадров не раз добавляли строки вручную — и он расходился с папкой
`public/assets/optimized`, пока следующий запуск генератора молча их не стирал.

Файл пересобирается командой, которая указана в сообщении. Хук возвращает
JSON-решение `{"decision": "deny", "reason": ...}` по контракту Antigravity.
"""
import json
import sys
from pathlib import PurePath

# Файл → чем он собирается.
GENERATED = {
    "src/views/portfolio-images.generated.ts": "yarn images",
}


def allow() -> int:
    print(json.dumps({"decision": "allow"}))
    return 0


def deny(reason: str) -> int:
    print(json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return allow()  # Непонятный ввод — не мешаем работе.

    tool_call = payload.get("toolCall") or {}
    args = tool_call.get("args") or {}
    raw_path = (
        args.get("Path")
        or args.get("TargetFile")
        or args.get("file_path")
        or args.get("path")
        or ""
    )
    if not raw_path:
        return allow()

    path = PurePath(str(raw_path).replace("\\", "/"))
    for generated, command in GENERATED.items():
        if path.as_posix().endswith(generated):
            return deny(
                f"{generated} — сгенерированный файл, руками не правится.\n"
                f"Пересобери его командой: {command}\n"
                "Если менять надо содержимое, а не файл, — правь источник: "
                "картинки в public/assets/optimized или сам генератор в tools/."
            )

    return allow()


if __name__ == "__main__":
    sys.exit(main())
