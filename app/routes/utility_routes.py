from fastapi import APIRouter, HTTPException

from app.controllers import (
    get_all_printer_connections,
    load_all_config_data,
    upload_box_label_structures_to_printers,
    upload_internal_label_structures_to_printers,
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
        pallet_label_response = upload_pallet_label_structures_to_printers(all_printers)
        box_label_response = upload_box_label_structures_to_printers(all_printers)
        internal_label_response = upload_internal_label_structures_to_printers(
            all_printers
        )

        return {
            "pallet": pallet_label_response,
            "box": box_label_response,
            "internal_labels": internal_label_response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
