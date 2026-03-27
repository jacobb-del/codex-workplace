import logging
from typing import Iterable

from parser import ItemRecord

LOGGER = logging.getLogger(__name__)


class ConsoleNotifier:
    """Simple notifier used as a stable extension point for Telegram/Discord later."""

    def send(self, items: Iterable[ItemRecord]) -> None:
        items = list(items)
        if not items:
            LOGGER.info("Notifier: no matching items to send")
            return

        for item in items:
            LOGGER.info(
                "Notifier item | %s | %.2f | %s | in_demand=%s | buyers=%s",
                item.title or item.item_id,
                item.price,
                item.item_url,
                item.in_demand,
                item.interested_buyers,
            )
