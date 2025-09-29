from fastapi import APIRouter, HTTPException

from app.controllers import (
    get_all_printer_connections,
    load_all_config_data,
    upload_box_label_structures_to_printers,
    upload_pallet_label_structures_to_printers,
)

label_utility_router = APIRouter()


@label_utility_router.on_event("startup")
def startup():
    load_all_config_data(logger=print)


@label_utility_router.post("/sync_label_structures")
async def upload_label_structures_to_all_printers():
    try:

        all_printers = get_all_printer_connections()
        print(f"all unique printer connections: {all_printers}")

        pallet_label_response = upload_pallet_label_structures_to_printers(all_printers)
        print(pallet_label_response)

        box_label_response = await upload_box_label_structures_to_printers(all_printers)
        print(box_label_response)

        return {"pallet": pallet_label_response, "box": box_label_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
