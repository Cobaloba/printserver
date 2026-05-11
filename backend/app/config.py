import os

PRINTER_VENDOR_ID = int(os.getenv("PRINTER_VENDOR_ID", "0x1ba0"), 16)
PRINTER_PRODUCT_ID = int(os.getenv("PRINTER_PRODUCT_ID", "0x220a"), 16)
PORT = int(os.getenv("PORT", "9000"))
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
API_KEY = os.getenv("API_KEY", "")  # empty = no auth (dev / trusted LAN)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # empty = bot disabled
_raw_allowed = os.getenv("TELEGRAM_ALLOWED_IDS", "")
TELEGRAM_ALLOWED_IDS: set[int] | None = (
    {int(x.strip()) for x in _raw_allowed.split(",") if x.strip()} if _raw_allowed else None
)  # None = open to all; set of ints = allowlist
