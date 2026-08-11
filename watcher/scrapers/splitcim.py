from __future__ import annotations

import logging
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from watcher.models import Product

log = logging.getLogger(__name__)

BASE_URL = "https://www.splitcim.com"
CATEGORY_URL = f"{BASE_URL}/kategori/az-kalan-siseler"
SOURCE = "splitcim"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

SKIP_NAMES = {
    "sepete ekle",
    "stokta yok",
    "şimdi incele",
    "incele",
    "tükendi",
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _looks_like_product_name(name: str) -> bool:
    lowered = name.lower()
    if lowered in SKIP_NAMES:
        return False
    if len(name) < 4:
        return False
    # Real listings almost always include volume.
    if not re.search(r"\d+\s*m/?l", name, flags=re.I):
        return False
    return True


def _find_price(node) -> str | None:
    current = node
    for _ in range(6):
        if current is None:
            break
        text = _clean(current.get_text(" ", strip=True))
        match = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2}\s*TL)", text)
        if match:
            return match.group(1)
        current = current.parent
    return None


def _parse_page(html: str) -> list[Product]:
    soup = BeautifulSoup(html, "lxml")
    products: dict[str, Product] = {}

    for a in soup.select('a[href*="/urun/"]'):
        href = a.get("href") or ""
        if "/urun/" not in href:
            continue

        title = _clean(a.get("title") or "")
        text = _clean(a.get_text(" ", strip=True))
        name = title if _looks_like_product_name(title) else text
        if not _looks_like_product_name(name):
            continue

        url = urljoin(BASE_URL, href.split("?")[0])
        slug = url.rstrip("/").split("/")[-1]
        if not slug:
            continue

        price = _find_price(a)
        existing = products.get(slug)
        if existing and existing.price and not price:
            continue

        products[slug] = Product(
            source=SOURCE,
            product_id=slug,
            name=name,
            url=url,
            price=price,
        )

    return list(products.values())


def _detect_max_page(html: str) -> int:
    pages = [int(p) for p in re.findall(r"az-kalan-siseler\?tp=(\d+)", html)]
    return max(pages) if pages else 1


def fetch_products(session: requests.Session | None = None, delay_sec: float = 0.3) -> list[Product]:
    sess = session or requests.Session()
    sess.headers.update(HEADERS)

    first = sess.get(CATEGORY_URL, timeout=45)
    first.raise_for_status()
    products = _parse_page(first.text)
    max_page = _detect_max_page(first.text)
    log.info("Splitcim: sayfa 1/%s -> %s ürün", max_page, len(products))

    by_id = {p.product_id: p for p in products}
    for page in range(2, max_page + 1):
        time.sleep(delay_sec)
        resp = sess.get(CATEGORY_URL, params={"tp": page}, timeout=45)
        resp.raise_for_status()
        page_products = _parse_page(resp.text)
        for product in page_products:
            by_id[product.product_id] = product
        log.info("Splitcim: sayfa %s/%s -> %s ürün", page, max_page, len(page_products))

    return list(by_id.values())
