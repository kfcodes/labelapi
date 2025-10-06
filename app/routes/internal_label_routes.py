from app.controllers import (
    blank_pallet_labels,
    get_pallet_label_printer,
    internal_product_id_and_description,
    large_blend_label_function,
    small_blend_label_function,
)
from fastapi import APIRouter, HTTPException, Request

internal_label_router = APIRouter()


@internal_label_router.post("/large_bulk_blend_label")
async def large_bulk_blend_label(request: Request):
    try:
        try:
            printer, site = await get_pallet_label_printer(request)
            body = await request.json()
        except Exception:
            body = {}

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
