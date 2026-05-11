import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.exceptions import PrinterError
from app.routers import health, print as print_router, status as status_router, admin as admin_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.dependencies import get_printer, get_status_cache
    from app.config import TELEGRAM_BOT_TOKEN
    cache = get_status_cache()
    try:
        printer = get_printer()
        cache.start(printer)
        if TELEGRAM_BOT_TOKEN:
            from app.services.telegram_bot import TelegramBot
            from app.config import TELEGRAM_ALLOWED_IDS
            from app.dependencies import set_telegram_bot
            bot = TelegramBot(TELEGRAM_BOT_TOKEN, allowed_ids=TELEGRAM_ALLOWED_IDS)
            bot.start(printer)
            set_telegram_bot(bot)
    except PrinterError as e:
        logger.warning("Printer unavailable at startup: %s — running in offline mode", e)
    yield


app = FastAPI(title="PrintServer", lifespan=lifespan)


@app.exception_handler(PrinterError)
async def printer_error_handler(request: Request, exc: PrinterError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


# API routers MUST be registered before StaticFiles mount
app.include_router(health.router)
app.include_router(print_router.router, prefix="/api/v1")
app.include_router(status_router.router)
app.include_router(admin_router.router)

# StaticFiles serves the SvelteKit SPA at "/" — must come last
_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
