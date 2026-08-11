from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Product:
    source: str
    product_id: str
    name: str
    url: str
    price: str | None = None

    @property
    def key(self) -> str:
        return f"{self.source}:{self.product_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
