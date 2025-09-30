from app.controllers import (
    blank_pallet_labels,
    blend_label_function,
    get_pallet_label_printer,
)
from fastapi import APIRouter, HTTPException, Request

internal_label_router = APIRouter()


@internal_label_router.post("/blend_label")
async def print_blend_label(request: Request):
    try:
        try:
            body = await request.json()
        except Exception:
            body = {}
        resp = await blend_label_function(body)
        return {"status": "ok", "zpl": resp, "received": body}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@internal_label_router.post("/blank_pallet_labels")
async def print_blank_pallet_labels(request: Request):
    try:
        printer, site = await get_pallet_label_printer(request)
        resp = await blank_pallet_labels(site, printer)
        return {resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
