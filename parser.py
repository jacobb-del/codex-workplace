import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class ItemRecord:
    item_id: str
    title: str = ""
    brand: str = ""
    price: float = 0.0
    size: str = ""
    condition: str = ""
    item_url: str = ""
    seller_name: str = ""
    interested_buyers: Optional[int] = None
    in_demand: bool = False

    def to_csv_row(self) -> Dict[str, Any]:
        return asdict(self)


_PRICE_RE = re.compile(r"([0-9]+(?:[\s.,][0-9]{3})*(?:[.,][0-9]{1,2})?)")
_INTEREST_RE = re.compile(r"(\d+)\s+buyers?\s+recently\s+sent\s+offers", re.IGNORECASE)


def parse_price(value: Any) -> float:
    """Parse prices like '€1,299.99', '1 299,99 PLN', '$300' into float."""
    if value is None:
        return 0.0

    text = str(value).strip()
    match = _PRICE_RE.search(text)
    if not match:
        return 0.0

    number = match.group(1).replace(" ", "")

    # Heuristic: if both separators exist, right-most is decimal separator.
    if "," in number and "." in number:
        if number.rfind(",") > number.rfind("."):
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")
    elif "," in number:
        parts = number.split(",")
        if len(parts[-1]) in (1, 2):
            number = ".".join(parts)
        else:
            number = "".join(parts)
    else:
        parts = number.split(".")
        if len(parts) > 1 and len(parts[-1]) not in (1, 2):
            number = "".join(parts)

    try:
        return float(number)
    except ValueError:
        return 0.0


def detect_in_demand(text: str) -> bool:
    return "in demand" in (text or "").lower()


def extract_interested_buyers(text: str) -> Optional[int]:
    match = _INTEREST_RE.search(text or "")
    return int(match.group(1)) if match else None


def normalize_item_id(raw: Any, item_url: str = "") -> str:
    if raw:
        return str(raw)

    match = re.search(r"/items/(\d+)", item_url or "")
    return match.group(1) if match else item_url
