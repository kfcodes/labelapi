from fastapi import APIRouter
from routes_layer.label_utility_routes import label_utility_router
from routes_layer.pallet_label_routes import pallet_label_router

router = APIRouter()

# Prefixes can be added here, or in individual files
# router.include_router(pallet_label_router, prefix="/labels")
router.include_router(pallet_label_router)
router.include_router(label_utility_router)
