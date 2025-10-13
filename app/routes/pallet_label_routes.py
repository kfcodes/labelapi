from fastapi import APIRouter, HTTPException, Request

from app.controllers import (
    generate_and_print_combo_label,
    get_pallet_label_printer,
    main_pallet_label_function,
)

pallet_label_router = APIRouter()


@pallet_label_router.post("/print_pallet_label/{pallet_id}")
async def print_pallet_label(pallet_id: int, request: Request):
    try:
        printer, site = await get_pallet_label_printer(request)
        resp = await main_pallet_label_function(site, printer, pallet_id)
        return {"status": "ok", "response": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@pallet_label_router.put("/stack_pallets")
async def print_combined_pallet_label(request: Request):
    """
    body:
    {
      "pallet_list": [123, 456],
      "height": 150
    }
    """
    try:
        body = await request.json()
        printer, _site = await get_pallet_label_printer(request)

        pallet_list = tuple(body["pallet_list"])
        combined_dimensions = int(body["height"])
        pallet_id = int(max(pallet_list))

        resp = await generate_and_print_combo_label(
            printer, pallet_id, combined_dimensions, pallet_list
        )
        return {"status": "ok", "response": resp}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
