import csv
import logging
import random
import time
from dataclasses import replace
from typing import Dict, List, Optional, Set

from playwright.sync_api import Browser, Page, TimeoutError, sync_playwright

from config import SELECTORS, ScraperConfig, ensure_output_dir
from parser import (
    ItemRecord,
    detect_in_demand,
    extract_interested_buyers,
    normalize_item_id,
    parse_price,
)

LOGGER = logging.getLogger(__name__)


class VintedScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.seen_ids: Set[str] = set()
        self.seen_urls: Set[str] = set()
        self.api_item_cache: Dict[str, Dict] = {}

    def run(self) -> List[ItemRecord]:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.config.headless)
            page = browser.new_page()
            page.set_default_timeout(self.config.timeout_ms)
            page.on("response", self._capture_api_response)

            self._try_accept_cookies(page)

            discovered: List[ItemRecord] = []
            for start_url in self.config.start_urls:
                if len(discovered) >= self.config.max_items_to_check:
                    break
                discovered.extend(self._scrape_search_url(page, start_url))

            enriched = self._enrich_records(browser, discovered)
            filtered = [
                item
                for item in enriched
                if item.price >= self.config.min_price and item.in_demand
            ]
            self._write_csv(filtered)
            browser.close()
            return filtered

    def _capture_api_response(self, response) -> None:
        """Capture lightweight item data from XHR/JSON responses when available."""
        url = response.url
        if "vinted" not in url:
            return
        if "application/json" not in response.headers.get("content-type", ""):
            return

        if "catalog" in url or "items" in url:
            try:
                payload = response.json()
            except Exception:
                return

            # Vinted shapes vary by locale/version, so attempt common keys.
            for key in ("items", "catalog_items", "results", "data"):
                value = payload.get(key) if isinstance(payload, dict) else None
                if isinstance(value, list):
                    for item in value:
                        item_id = normalize_item_id(item.get("id"), item.get("url", ""))
                        self.api_item_cache[item_id] = item

    def _scrape_search_url(self, page: Page, start_url: str) -> List[ItemRecord]:
        LOGGER.info("Opening search URL: %s", start_url)

        for attempt in range(1, self.config.max_retries + 1):
            try:
                page.goto(start_url, wait_until="domcontentloaded")
                self._human_delay()
                break
            except TimeoutError:
                LOGGER.warning("Timeout opening %s (attempt %s)", start_url, attempt)
                if attempt == self.config.max_retries:
                    return []

        records: List[ItemRecord] = []
        for _ in range(self.config.scroll_rounds):
            page.mouse.wheel(0, 3000)
            self._human_delay()
            cards = page.locator(SELECTORS["listing_card"])
            card_count = cards.count()
            LOGGER.debug("Loaded %s cards", card_count)
            if card_count >= self.config.max_items_to_check:
                break

        link_locator = page.locator(SELECTORS["listing_link"])
        total_links = min(link_locator.count(), self.config.max_items_to_check)
        LOGGER.info("Found %s candidate items", total_links)

        for idx in range(total_links):
            href = link_locator.nth(idx).get_attribute("href")
            if not href:
                continue
            url = href if href.startswith("http") else f"https://www.vinted.com{href}"

            record = self._record_from_card_or_api(url)
            if not record:
                continue
            if self._is_duplicate(record):
                continue
            records.append(record)

        return records

    def _record_from_card_or_api(self, item_url: str) -> Optional[ItemRecord]:
        item_id = normalize_item_id(None, item_url)
        raw = self.api_item_cache.get(item_id, {})

        title = raw.get("title") or ""
        brand = raw.get("brand_title") or raw.get("brand") or ""
        price = parse_price(raw.get("price") or raw.get("total_item_price") or 0)
        size = raw.get("size_title") or raw.get("size") or ""
        condition = raw.get("status") or raw.get("item_condition") or ""
        seller = ""
        user_data = raw.get("user")
        if isinstance(user_data, dict):
            seller = user_data.get("login") or user_data.get("name") or ""

        demand_text = str(raw.get("badges") or "") + " " + str(raw.get("description") or "")
        in_demand = detect_in_demand(demand_text)
        interested = extract_interested_buyers(demand_text)

        return ItemRecord(
            item_id=item_id,
            title=title,
            brand=brand,
            price=price,
            size=size,
            condition=condition,
            item_url=item_url,
            seller_name=seller,
            interested_buyers=interested,
            in_demand=in_demand,
        )

    def _enrich_records(self, browser: Browser, records: List[ItemRecord]) -> List[ItemRecord]:
        """Visit item pages only when API/card data is incomplete (or no in-demand data)."""
        if not records:
            return []

        detail_page = browser.new_page()
        detail_page.set_default_timeout(self.config.timeout_ms)
        result: List[ItemRecord] = []

        for item in records[: self.config.max_items_to_check]:
            if self._has_enough_data(item):
                result.append(item)
                continue

            enriched = self._fetch_detail_with_retries(detail_page, item)
            result.append(enriched or item)
            self._human_delay()

        detail_page.close()
        return result

    def _fetch_detail_with_retries(self, page: Page, item: ItemRecord) -> Optional[ItemRecord]:
        for attempt in range(1, self.config.max_retries + 1):
            try:
                page.goto(item.item_url, wait_until="domcontentloaded")
                page.wait_for_selector(SELECTORS["title"], timeout=self.config.timeout_ms)

                body_text = page.inner_text("body")
                in_demand = detect_in_demand(body_text)
                interested = extract_interested_buyers(body_text)

                title = self._safe_text(page, SELECTORS["title"]) or item.title
                price = parse_price(self._safe_text(page, SELECTORS["price"]) or item.price)
                brand = self._safe_text(page, SELECTORS["brand"]) or item.brand
                size = self._safe_text(page, SELECTORS["size"]) or item.size
                condition = self._safe_text(page, SELECTORS["condition"]) or item.condition
                seller = self._safe_text(page, SELECTORS["seller"]) or item.seller_name

                return replace(
                    item,
                    title=title,
                    brand=brand,
                    price=price,
                    size=size,
                    condition=condition,
                    seller_name=seller,
                    in_demand=in_demand or item.in_demand,
                    interested_buyers=interested if interested is not None else item.interested_buyers,
                )
            except Exception as exc:
                LOGGER.warning(
                    "Detail fetch failed for %s (attempt %s/%s): %s",
                    item.item_url,
                    attempt,
                    self.config.max_retries,
                    exc,
                )
        return None

    @staticmethod
    def _safe_text(page: Page, selector: str) -> str:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                return ""
            return (locator.inner_text() or "").strip()
        except Exception:
            return ""

    def _has_enough_data(self, item: ItemRecord) -> bool:
        return bool(item.title and item.price > 0 and item.in_demand)

    def _is_duplicate(self, item: ItemRecord) -> bool:
        if item.item_id in self.seen_ids or item.item_url in self.seen_urls:
            return True
        self.seen_ids.add(item.item_id)
        self.seen_urls.add(item.item_url)
        return False

    def _human_delay(self) -> None:
        lo, hi = self.config.delay_range_seconds
        time.sleep(random.uniform(lo, hi))

    def _try_accept_cookies(self, page: Page) -> None:
        try:
            page.goto("https://www.vinted.com", wait_until="domcontentloaded")
            btn = page.locator(SELECTORS["cookie_accept"]).first
            if btn.count() > 0:
                btn.click(timeout=2_000)
                LOGGER.info("Cookie banner accepted")
        except Exception:
            LOGGER.debug("Cookie banner not found or could not be accepted")

    def _write_csv(self, records: List[ItemRecord]) -> None:
        output_path = ensure_output_dir(self.config.output_filename)
        LOGGER.info("Writing %s rows to %s", len(records), output_path)

        with output_path.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = [
                "item_id",
                "title",
                "brand",
                "price",
                "size",
                "condition",
                "item_url",
                "seller_name",
                "interested_buyers",
                "in_demand",
            ]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in records:
                writer.writerow(row.to_csv_row())


def run_scraper(config: ScraperConfig) -> List[ItemRecord]:
    scraper = VintedScraper(config)
    return scraper.run()
