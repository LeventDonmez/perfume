from __future__ import annotations

import logging
import time

import requests

log = logging.getLogger(__name__)


def send_telegram_message(token: str, chat_id: str, text: str, max_retries: int = 5) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": False,
    }

    for attempt in range(1, max_retries + 1):
        response = requests.post(url, json=payload, timeout=30)
        if response.ok:
            return

        if response.status_code == 429:
            retry_after = 5
            try:
                retry_after = int(response.json().get("parameters", {}).get("retry_after", retry_after))
            except Exception:  # noqa: BLE001
                pass
            log.warning(
                "Telegram rate limit, %ss bekleniyor (deneme %s/%s)",
                retry_after,
                attempt,
                max_retries,
            )
            time.sleep(retry_after + 1)
            continue

        log.error("Telegram error %s: %s", response.status_code, response.text)
        response.raise_for_status()

    response.raise_for_status()
