from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import get_printer
from app.services.printer import PrinterInterface
from app.services import print_service
from app.models.print_models import (
    TodoRequest, ReceiptRequest, FreeTextRequest, QrRequest,
)

router = APIRouter(prefix="/print", tags=["print"])
PrinterDep = Annotated[PrinterInterface, Depends(get_printer)]


@router.post("/todo")
def print_todo(req: TodoRequest, printer: PrinterDep):
    print_service.print_todo(printer, req.title, req.items)
    return {"success": True}


@router.post("/receipt")
def print_receipt(req: ReceiptRequest, printer: PrinterDep):
    items = [(item.name, item.price) for item in req.items]
    print_service.print_receipt(printer, req.store, items, req.address, req.phone, req.tax_pct)
    return {"success": True}


@router.post("/free-text")
def print_free_text(req: FreeTextRequest, printer: PrinterDep):
    print_service.print_free_text(printer, req.text, req.font_size)
    return {"success": True}


@router.post("/qr")
def print_qr(req: QrRequest, printer: PrinterDep):
    print_service.print_qr(printer, req.url)
    return {"success": True}


@router.post("/goatse")
def print_goatse(printer: PrinterDep):
    print_service.print_goatse(printer)
    return {"success": True}
