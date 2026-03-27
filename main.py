import argparse
import logging
from typing import Optional

from config import ScraperConfig
from notifier import ConsoleNotifier
from scraper import run_scraper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vinted in-demand item scraper")
    parser.add_argument("--min-price", type=float, default=None, help="Minimum item price")
    parser.add_argument("--max-items", type=int, default=None, help="Maximum items to check")
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser in headed mode (overrides config.headless)",
    )
    parser.add_argument(
        "--start-url",
        action="append",
        default=None,
        help="Provide one or more Vinted search URLs (can be repeated)",
    )
    parser.add_argument("--output", default=None, help="Output CSV path")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console logging level",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> ScraperConfig:
    cfg = ScraperConfig()
    if args.min_price is not None:
        cfg.min_price = args.min_price
    if args.max_items is not None:
        cfg.max_items_to_check = args.max_items
    if args.headful:
        cfg.headless = False
    if args.start_url:
        cfg.start_urls = args.start_url
    if args.output:
        cfg.output_filename = args.output
    return cfg


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def main() -> Optional[int]:
    args = parse_args()
    setup_logging(args.log_level)
    config = build_config(args)

    logging.getLogger(__name__).info(
        "Starting Vinted scraper: min_price=%s, max_items=%s, headless=%s",
        config.min_price,
        config.max_items_to_check,
        config.headless,
    )

    results = run_scraper(config)
    ConsoleNotifier().send(results)
    logging.getLogger(__name__).info(
        "Done. %s matching items saved to %s",
        len(results),
        config.output_filename,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
