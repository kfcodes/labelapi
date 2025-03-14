# fastapi imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# pallet operations
from routes_layer.api.pallet_label_routes import pallet_label_router

import os
from dotenv import load_dotenv
load_dotenv(".env")

app = FastAPI();

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pallet_label_router)
