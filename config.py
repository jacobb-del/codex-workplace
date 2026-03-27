from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class ScraperConfig:
    """Configuration for Vinted scraping run."""

    start_urls: List[str] = field(
        default_factory=lambda: [
            # Replace with your own Vinted search/category URLs.
            "https://www.vinted.com/catalog?order=newest_first"
        ]
    )
    min_price: float = 300.0
    max_items_to_check: int = 200
    headless: bool = True
    timeout_ms: int = 20_000
    max_retries: int = 3
    scroll_rounds: int = 20
    delay_range_seconds: Tuple[float, float] = (1.2, 2.8)
    output_filename: str = "output/results.csv"

    # Helpful for staged rollouts (e.g., local testing only first page).
    max_pages_per_url: int = 1


SELECTORS: Dict[str, str] = {
    "cookie_accept": "button:has-text('Accept all')",
    "listing_card": "[data-testid='catalog-item'], .feed-grid__item, .ItemBox",
    "listing_link": "a[href*='/items/'], a.new-item-box__overlay",
    "title": "h1[data-testid='item-title'], h1.web_ui__Text__text",
    "price": "[data-testid='item-price'], .item-price, .web_ui__Text__title",
    "brand": "[data-testid='item-brand'], a[href*='brand']",
    "size": "[data-testid='item-size'], .details-list__item:has-text('Size')",
    "condition": "[data-testid='item-status'], .details-list__item:has-text('Condition')",
    "seller": "[data-testid='profile-username'], a[href*='/member/']",
    "in_demand": "text=/In demand!?/i",
}


def ensure_output_dir(path: str) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path
