from fastapi import APIRouter

from .box_label_routes import box_label_router
from .internal_label_routes import internal_label_router
from .label_utility_routes import label_utility_router
from .pallet_label_routes import pallet_label_router

router = APIRouter()
router.include_router(box_label_router)
router.include_router(internal_label_router)
router.include_router(label_utility_router)
router.include_router(pallet_label_router)

__all__ = ["router"]
