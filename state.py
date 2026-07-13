import json
import logging
import os
from collections import deque

logger = logging.getLogger(__name__)


class AlertState:
    """Geziene alert-ID's en historie, met atomaire opslag op schijf."""

    def __init__(self, max_seen_ids: int, history_size: int):
        self.max_seen_ids = max_seen_ids
        self.history_size = history_size
        self.seen_ids = set()
        self.seen_order = deque()
        self.history: list[dict] = []

    def is_seen(self, alert_id: str) -> bool:
        return alert_id in self.seen_ids

    def remember(self, alert_id: str) -> None:
        """Onthoudt een alert-ID, begrensd tot max_seen_ids zodat het
        geheugengebruik (en het state-bestand) niet onbeperkt groeit."""
        if alert_id in self.seen_ids:
            return

        self.seen_ids.add(alert_id)
        self.seen_order.append(alert_id)

        while len(self.seen_order) > self.max_seen_ids:
            oldest = self.seen_order.popleft()
            self.seen_ids.discard(oldest)

    def add_history(self, payload: dict) -> None:
        self.history.insert(0, payload)
        del self.history[self.history_size:]

    def load(self, path: str) -> None:
        """Laadt seen_ids en historie van schijf, zodat een herstart van de
        container niet leidt tot het opnieuw publiceren van oude meldingen."""
        if not os.path.exists(path):
            logger.info("Geen bestaande state gevonden op %s, start leeg", path)
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for alert_id in data.get("seen_ids", []):
                self.remember(alert_id)

            self.history = data.get("history", [])[: self.history_size]

            logger.info(
                "State geladen: %d bekende meldingen, %d in historie",
                len(self.seen_ids),
                len(self.history),
            )
        except Exception as exc:
            logger.warning("Kon state niet laden (%s), start met lege state", exc)

    def save(self, path: str) -> None:
        """Schrijft eerst naar een tijdelijk bestand en vervangt daarna pas het
        echte state-bestand, zodat een crash tijdens het schrijven nooit een
        corrupt state.json achterlaat."""
        tmp_file = f"{path}.tmp"

        try:
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"seen_ids": list(self.seen_order), "history": self.history},
                    f,
                    ensure_ascii=False,
                )
            os.replace(tmp_file, path)
        except Exception as exc:
            logger.warning("Kon state niet opslaan: %s", exc)
