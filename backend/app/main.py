import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.exceptions import PrinterError
from app.routers import health, print as print_router

app = FastAPI(title="PrintServer")


@app.exception_handler(PrinterError)
async def printer_error_handler(request: Request, exc: PrinterError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


# API routers MUST be registered before StaticFiles mount
app.include_router(health.router)
app.include_router(print_router.router, prefix="/api/v1")

# StaticFiles serves the SvelteKit SPA at "/" — must come last
_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
