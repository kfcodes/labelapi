from app.controller import blend_label_function  # internal label controller
from fastapi import APIRouter, HTTPException, Request

internal_label_router = APIRouter()


@internal_label_router.post("/blend")
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
