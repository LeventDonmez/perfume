from __future__ import annotations

import argparse
import logging
import os
import random
import sys
from datetime import timedelta
from pathlib import Path

import requests

from watcher.models import Product
from watcher.scrapers import dekant, splitcim
from watcher.state import StateStore, utc_now
from watcher.telegram_notify import send_telegram_message

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE = ROOT / "data" / "state.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("watcher")


def format_product_message(product: Product) -> str:
    source_label = {
        "dekant": "Dekant Parfüm Depo",
        "splitcim": "Splitcim",
    }.get(product.source, product.source)

    lines = [
        f"Yeni ürün — {source_label}",
        product.name,
    ]
    if product.price:
        lines.append(product.price)
    lines.append(product.url)
    return "\n".join(lines)


def collect_products() -> list[Product]:
    session = requests.Session()
    products: list[Product] = []
    errors: list[str] = []

    for label, fetcher in (
        ("dekant", dekant.fetch_products),
        ("splitcim", splitcim.fetch_products),
    ):
        try:
            items = fetcher(session=session)
            log.info("%s: %s ürün alındı", label, len(items))
            products.extend(items)
        except Exception as exc:  # noqa: BLE001 - surface scraper failures without aborting all
            msg = f"{label} scrape failed: {exc}"
            log.exception(msg)
            errors.append(msg)

    if not products and errors:
        raise RuntimeError("; ".join(errors))
    return products


def run(force: bool = False, dry_run: bool = False, state_path: Path = DEFAULT_STATE) -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not dry_run and (not token or not chat_id):
        raise SystemExit("TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID gerekli (veya --dry-run kullan)")

    store = StateStore(state_path)
    now = utc_now()

    if not force and store.next_check_at and now < store.next_check_at:
        log.info("Erken çıkış: sonraki kontrol %s", store.next_check_at.isoformat())
        return 0

    products = collect_products()
    seen = store.seen
    new_products: list[Product] = []

    for product in products:
        if product.key not in seen:
            new_products.append(product)
        seen[product.key] = {
            "name": product.name,
            "url": product.url,
            "price": product.price,
            "last_seen_at": now.isoformat(),
        }

    if not store.bootstrapped:
        log.info(
            "İlk çalıştırma: %s ürün kaydedildi, bildirim gönderilmedi",
            len(products),
        )
        store.bootstrapped = True
        new_products = []
    elif new_products:
        log.info("%s yeni ürün bulundu", len(new_products))
        for product in new_products:
            message = format_product_message(product)
            if dry_run:
                log.info("DRY-RUN mesaj:\n%s", message)
            else:
                send_telegram_message(token, chat_id, message)
                log.info("Bildirim gönderildi: %s", product.name)
    else:
        log.info("Yeni ürün yok")

    interval_min = random.randint(7, 13)
    store.last_check_at = now
    store.next_check_at = now + timedelta(minutes=interval_min)
    store.save()
    log.info("Sonraki kontrol ~%s dakika sonra (%s)", interval_min, store.next_check_at.isoformat())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parfüm stok watcher")
    parser.add_argument("--force", action="store_true", help="Rastgele aralık kontrolünü atla")
    parser.add_argument("--dry-run", action="store_true", help="Telegram göndermeden çalıştır")
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE,
        help="State JSON yolu",
    )
    args = parser.parse_args(argv)
    return run(force=args.force, dry_run=args.dry_run, state_path=args.state)


if __name__ == "__main__":
    sys.exit(main())
