# fastapi imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# pallet operations
from routes_layer import *

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
# app.include_router(box_label_routes)
