from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)


def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        },
        timeout=30,
    )
    if not response.ok:
        log.error("Telegram error %s: %s", response.status_code, response.text)
        response.raise_for_status()
