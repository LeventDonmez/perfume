from __future__ import annotations

import html
import logging
import math
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from watcher.models import Product

log = logging.getLogger(__name__)

BASE_URL = "https://www.dekantparfumdepo.com/"
SOURCE = "dekant"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}


def _clean_text(value: str) -> str:
    text = html.unescape(html.unescape(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def _parse_total_count(page_html: str) -> int | None:
    match = re.search(r'"totalCount"\s*:\s*(\d+)', page_html)
    if not match:
        return None
    return int(match.group(1))


def _parse_products(page_html: str) -> list[Product]:
    soup = BeautifulSoup(page_html, "lxml")
    products: list[Product] = []
    seen_ids: set[str] = set()

    for container in soup.select('[data-hook="product-item-root"], [data-hook="product-item-container"]'):
        link = container.select_one('a[href*="/product-page/"]')
        name_el = container.select_one('[data-hook="product-item-name"]')
        price_el = container.select_one(
            '[data-hook="product-item-price-to-pay"], [data-hook="product-item-price"]'
        )
        if not link or not name_el:
            continue

        href = link.get("href") or ""
        url = urljoin(BASE_URL, href)
        slug = url.rstrip("/").split("/")[-1]
        if not slug or slug in seen_ids:
            continue

        seen_ids.add(slug)
        products.append(
            Product(
                source=SOURCE,
                product_id=slug,
                name=_clean_text(name_el.get_text(" ", strip=True)),
                url=url,
                price=_clean_text(price_el.get_text(" ", strip=True)) if price_el else None,
            )
        )

    if products:
        return products

    # Fallback: regex on SSR markup if DOM hooks change.
    for href, name in re.findall(
        r'href="(https://www\.dekantparfumdepo\.com/product-page/[^"]+)"[^>]*>[\s\S]*?'
        r'data-hook="product-item-name"[^>]*>([^<]+)',
        page_html,
    ):
        slug = href.rstrip("/").split("/")[-1]
        if slug in seen_ids:
            continue
        seen_ids.add(slug)
        products.append(
            Product(
                source=SOURCE,
                product_id=slug,
                name=_clean_text(name),
                url=href,
            )
        )
    return products


def fetch_products(session: requests.Session | None = None, delay_sec: float = 0.4) -> list[Product]:
    sess = session or requests.Session()
    sess.headers.update(HEADERS)

    first = sess.get(BASE_URL, timeout=45)
    first.raise_for_status()
    first_html = first.text
    page_products = _parse_products(first_html)
    if not page_products:
        raise RuntimeError("Dekant: ilk sayfada ürün bulunamadı")

    total_count = _parse_total_count(first_html) or len(page_products)
    per_page = len(page_products)
    total_pages = max(1, math.ceil(total_count / per_page))
    log.info("Dekant: %s ürün, %s sayfa (sayfa başı ~%s)", total_count, total_pages, per_page)

    by_id: dict[str, Product] = {p.product_id: p for p in page_products}

    for page in range(2, total_pages + 1):
        time.sleep(delay_sec)
        resp = sess.get(BASE_URL, params={"page": page}, timeout=45)
        resp.raise_for_status()
        products = _parse_products(resp.text)
        if not products:
            log.warning("Dekant: sayfa %s boş, duruyor", page)
            break
        for product in products:
            by_id[product.product_id] = product
        log.info("Dekant: sayfa %s/%s -> %s ürün (toplam unique %s)", page, total_pages, len(products), len(by_id))

    return list(by_id.values())
