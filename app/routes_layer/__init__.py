from fastapi import APIRouter

from routes_layer.pallet_label_routes import pallet_label_router
from routes_layer.printer_data_routes import printer_controller_router

router = APIRouter()

# Prefixes can be added here, or in individual files
# router.include_router(pallet_label_router, prefix="/labels")
router.include_router(pallet_label_router)
router.include_router(printer_controller_router)
