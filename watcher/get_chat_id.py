"""Telegram grup chat id bulmaya yardımcı script.

Kullanım:
  set TELEGRAM_BOT_TOKEN=...
  python -m watcher.get_chat_id
"""

from __future__ import annotations

import json
import os
import sys

import requests


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN gerekli", file=sys.stderr)
        return 1

    response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    chats: dict[str, str] = {}
    for update in payload.get("result", []):
        message = update.get("message") or update.get("my_chat_member") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            continue
        title = chat.get("title") or chat.get("username") or chat.get("first_name") or "?"
        chats[str(chat_id)] = f"{chat.get('type', '?')}: {title}"

    if not chats:
        print(
            "Hiç chat bulunamadı.\n"
            "1) Botu gruba ekle\n"
            "2) Gruba bir mesaj yaz\n"
            "3) Bu komutu tekrar çalıştır"
        )
        return 2

    print("Bulunan chat'ler:")
    for chat_id, label in chats.items():
        print(f"  {chat_id}  ->  {label}")
    print("\nTELEGRAM_CHAT_ID olarak grup id'sini kullan (genelde -100 ile başlar).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
