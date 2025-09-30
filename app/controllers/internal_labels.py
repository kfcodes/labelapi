from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Mapping, Tuple, Union

from app.database.read_db import read_db, read_to_list_index
from app.database.write_db import update_pallet_packing_list, write_db
from app.printer_connection.zpl_printer_logic import label_printer_connection
from app.static_json_readers import (
    get_all_pallet_label_zpl,
    get_pallet_label_zpl,
    validate_fn_usage,
)
from app.zpl.pallet_label_zpl_logic import create_pallet_label_zpl
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / "env" / "label_variables.env")


from app.printer_connection.zpl_printer_logic import (
    label_printer_connection,
)  # kept for future use (currently commented)
from app.zpl.internal_label_zpl_logic import create_blend_label_zpl


# async def blend_label_function(site,printer, body):
async def blend_label_function(body):
    try:
        label_structure_name = "INTBLND"
        pallet_label_zpl = create_blend_label_zpl(
            label_structure_name, body["blend_id"], body["allergens"]
        )
        # response = label_printer_connection(
        #     pallet_label_zpl, printer["ip"], printer["port"]
        # )
        # return response
        return pallet_label_zpl

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


async def blank_pallet_labels(site, printer):
    try:
        label_structure_name = "INTBLNK"
        pallet_label_zpl = create_blend_label_zpl()
        return pallet_label_zpl

    except Exception as ex:
        print("Label could not be created due to: \n", ex)
