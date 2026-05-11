from typing import Annotated
from fastapi import APIRouter, Depends
from app.auth import require_api_key
from app.dependencies import get_printer, get_roll_tracker
from app.services.printer import PrinterInterface
from app.services.roll_tracker import RollTracker
from app.services import print_service
from app.models.print_models import (
    TodoRequest, ReceiptRequest, FreeTextRequest, QrRequest,
)

router = APIRouter(prefix="/print", tags=["print"], dependencies=[Depends(require_api_key)])
PrinterDep = Annotated[PrinterInterface, Depends(get_printer)]
TrackerDep = Annotated[RollTracker, Depends(get_roll_tracker)]


@router.post("/todo")
def print_todo(req: TodoRequest, printer: PrinterDep, tracker: TrackerDep):
    print_service.print_todo(printer, req.title, req.items)
    tracker.add_bytes(printer.get_bytes_for_job())
    return {"success": True}


@router.post("/receipt")
def print_receipt(req: ReceiptRequest, printer: PrinterDep, tracker: TrackerDep):
    items = [(item.name, item.price) for item in req.items]
    print_service.print_receipt(printer, req.store, items, req.address, req.phone, req.tax_pct)
    tracker.add_bytes(printer.get_bytes_for_job())
    return {"success": True}


@router.post("/free-text")
def print_free_text(req: FreeTextRequest, printer: PrinterDep, tracker: TrackerDep):
    print_service.print_free_text(printer, req.text, req.font_size)
    tracker.add_bytes(printer.get_bytes_for_job())
    return {"success": True}


@router.post("/qr")
def print_qr(req: QrRequest, printer: PrinterDep, tracker: TrackerDep):
    print_service.print_qr(printer, req.url)
    tracker.add_bytes(printer.get_bytes_for_job())
    return {"success": True}


@router.post("/goatse")
def print_goatse(printer: PrinterDep, tracker: TrackerDep):
    print_service.print_goatse(printer)
    tracker.add_bytes(printer.get_bytes_for_job())
    return {"success": True}
