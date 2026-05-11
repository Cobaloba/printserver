import os

PRINTER_VENDOR_ID = int(os.getenv("PRINTER_VENDOR_ID", "0x1ba0"), 16)
PRINTER_PRODUCT_ID = int(os.getenv("PRINTER_PRODUCT_ID", "0x220a"), 16)
PORT = int(os.getenv("PORT", "9000"))
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
API_KEY = os.getenv("API_KEY", "")  # empty = no auth (dev / trusted LAN)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # empty = bot disabled
