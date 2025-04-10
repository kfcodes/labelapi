from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes_layer import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pallet_label_router)
app.include_router(printer_controller_router)
# app.include_router(box_label_routes)
