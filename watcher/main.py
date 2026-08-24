from __future__ import annotations

import argparse
import logging
import os
import random
import sys
import time
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


def collect_products() -> tuple[list[Product], set[str]]:
    session = requests.Session()
    products: list[Product] = []
    succeeded: set[str] = set()
    errors: list[str] = []

    for label, fetcher in (
        ("dekant", dekant.fetch_products),
        ("splitcim", splitcim.fetch_products),
    ):
        try:
            items = fetcher(session=session)
            log.info("%s: %s ürün alındı", label, len(items))
            products.extend(items)
            succeeded.add(label)
        except Exception as exc:  # noqa: BLE001 - bir kaynak düşse diğerini sürdür
            msg = f"{label} scrape failed: {exc}"
            log.exception(msg)
            errors.append(msg)

    if not products and errors:
        raise RuntimeError("; ".join(errors))
    return products, succeeded


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

    products, succeeded_sources = collect_products()
    seen = store.seen
    already_bootstrapped = store.bootstrapped_sources
    new_products: list[Product] = []
    first_seen_by_source: dict[str, int] = {}

    for product in products:
        if product.source not in succeeded_sources:
            continue

        is_new = product.key not in seen
        seen[product.key] = {
            "name": product.name,
            "url": product.url,
            "price": product.price,
            "last_seen_at": now.isoformat(),
        }

        if not is_new:
            continue

        if product.source not in already_bootstrapped:
            first_seen_by_source[product.source] = first_seen_by_source.get(product.source, 0) + 1
            continue

        new_products.append(product)

    for source in succeeded_sources:
        if source not in already_bootstrapped:
            count = first_seen_by_source.get(source, 0)
            log.info(
                "%s ilk kez başarılı: %s ürün kaydedildi, bildirim yok",
                source,
                count,
            )
            store.mark_source_bootstrapped(source)

    interval_min = random.randint(2, 5)
    store.last_check_at = now
    store.next_check_at = now + timedelta(minutes=interval_min)
    # Bildirimden önce kaydet: yarım kalan gönderimde tekrar spam olmasın.
    store.save()

    if new_products:
        log.info("%s yeni ürün bulundu", len(new_products))
        for product in new_products:
            message = format_product_message(product)
            if dry_run:
                log.info("DRY-RUN mesaj:\n%s", message)
            else:
                send_telegram_message(token, chat_id, message)
                log.info("Bildirim gönderildi: %s", product.name)
                time.sleep(1.2)
    else:
        log.info("Yeni ürün yok")

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
