import threading
import time
import logging

logger = logging.getLogger(__name__)

_DEFAULT_STATE = {
    "printer_online": False,
    "paper_near_end": False,
    "paper_out": False,
    "estimated_remaining_pct": 0,
}
POLL_INTERVAL = 5


class StatusCache:
    def __init__(self):
        self._cache: dict = dict(_DEFAULT_STATE)
        self._lock = threading.Lock()

    def start(self, printer) -> None:
        thread = threading.Thread(
            target=self._poll_loop, args=(printer,), daemon=True
        )
        thread.start()

    def _poll_loop(self, printer) -> None:
        while True:
            try:
                status = printer.get_status()
                with self._lock:
                    self._cache.update(status)
                    self._cache.setdefault("estimated_remaining_pct", 0)
            except Exception as e:
                logger.debug("Status poll failed: %s", e)
                with self._lock:
                    self._cache["printer_online"] = False
            time.sleep(POLL_INTERVAL)

    def get_cached(self) -> dict:
        with self._lock:
            return dict(self._cache)
