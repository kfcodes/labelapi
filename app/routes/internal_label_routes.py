from fastapi import APIRouter, HTTPException, Request

from app.controllers import (
    blank_pallet_labels,
    get_goodsin_label_printer,
    get_pallet_label_printer,
    goodsin_label_function,
    internal_product_id_and_description,
    large_blend_label_function,
    small_blend_label_function,
)
from app.schemas.goodsin_labels import GoodsInLabelBatch

internal_label_router = APIRouter()


@internal_label_router.post("/large_bulk_blend_label")
async def large_bulk_blend_label(request: Request):
    try:
        body = await request.json()
        printer, _site = await get_pallet_label_printer(request)

        print(body)

        resp = await large_blend_label_function(body, printer)

        return {"status": "ok", "zpl": resp, "received": body}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@internal_label_router.post("/small_bulk_blend_label")
async def small_bulk_blend_label(request: Request):
    try:
        printer, site = await get_pallet_label_printer(request)
        resp = await small_blend_label_function(printer)

        return {"status": "ok", "zpl": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@internal_label_router.post("/product_id_and_description_label/:id/:qty")
async def print_blend_label(request: Request, id: str, qty: int):
    try:
        printer, site = await get_pallet_label_printer(request)
        resp = await internal_product_id_and_description(id, qty, printer)

        return {"status": "ok", "zpl": resp, "received": id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@internal_label_router.post("/blank_pallet_labels")
async def print_blank_pallet_labels(request: Request):
    try:
        printer, site = await get_pallet_label_printer(request)
        resp = await blank_pallet_labels(printer)

        return {"status": "ok", "zpl": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@internal_label_router.post("/goodsin_labels")
async def print_goodsin_labels_function(request: Request, batch: GoodsInLabelBatch):
    printer, site = await get_goodsin_label_printer(request)

    labels = [item.model_dump() for item in batch.labels]

    resp = await goodsin_label_function(labels=labels, printer=printer)

    return {
        "status": "ok",
        "count": len(labels),
        "printer": {"ip": printer.get("ip"), "port": printer.get("port")},
        "result": str(resp),
    }
