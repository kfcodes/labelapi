from fastapi import APIRouter, HTTPException, Request

from app.controllers import test_label_function

test_label_router = APIRouter()


@test_label_router.post("/test_label")
async def test_label(request: Request):
    try:
        # printer, site = await get_test_label_printer(request)
        # resp = await test_label_function(printer)
        response = await test_label_function()

        return {"status": "ok", "zpl": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
