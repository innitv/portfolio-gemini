# -*- coding: utf-8 -*-
"""
Защитник: файл с доступами к хостингу не читается и не показывается.

В `.env.portfolio-deploy` лежат логин и пароль FTP. Они нужны скриптам выгрузки,
но не нужны ни в контексте разговора, ни в выводе команды: всё, что прочитано,
рано или поздно оказывается в тексте ответа, в логе задачи или в отчёте.

Хук закрывает два пути: чтение файла инструментом и вывод его содержимого
командой (`cat`, `type`, `Get-Content`). Записи он не запрещает — файл создают и
правят, просто не читая вслух.

Проверить заполненность можно, не раскрывая значений: скрипт, который печатает
длину и признак «заглушка из примера», — в `tools/`.
"""
import json
import re
import sys

SECRET = ".env.portfolio-deploy"

# Команды, которые высыпают файл в вывод. `grep` и `sed` сюда же: их часто зовут
# «посмотреть одну строку», а строка — как раз с паролем.
DUMPERS = (
    "cat", "type", "more", "less", "head", "tail",
    "grep", "sed", "awk", "get-content", "gc",
)


def allow() -> int:
    print(json.dumps({"decision": "allow"}))
    return 0


def deny(reason: str) -> int:
    print(json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False))
    return 0


def dumps_secret(command: str) -> bool:
    """
    Опасно ли звено команды.

    🔴 Разбор по звеньям, а не поиск по всей строке. Первая версия ловила имя
    файла где угодно — и заблокировала команду, где оно лежало внутри `echo`
    как тестовые данные. Звено опасно, только если САМО начинается с выводящей
    команды и содержит имя файла.
    """
    for chunk in re.split(r"&&|\|\||[|;&\n]", command.replace("\\", "/")):
        words = chunk.strip().split()
        if not words or SECRET not in chunk:
            continue
        head = words[0].lstrip("(").rsplit("/", 1)[-1].lower()
        if head in DUMPERS:
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return allow()

    tool_call = payload.get("toolCall") or {}
    tool = tool_call.get("name", "")
    args = tool_call.get("args") or {}

    if tool in ("read_file", "view_file"):
        path = str(
            args.get("Path")
            or args.get("AbsolutePath")
            or args.get("file_path")
            or ""
        ).replace("\\", "/")
        if path.endswith(SECRET):
            return deny(
                f"{SECRET} содержит логин и пароль FTP — читать его не нужно.\n"
                "Скриптам выгрузки он доступен и так; для проверки заполненности "
                "есть разбор, который печатает только длину полей."
            )

    if tool == "run_command":
        command = str(args.get("CommandLine") or args.get("command") or "")
        if dumps_secret(command):
            return deny(
                f"Команда выводит содержимое {SECRET} — там пароль FTP.\n"
                "Читай из него значения программой, которая их не печатает."
            )

    return allow()


if __name__ == "__main__":
    sys.exit(main())
