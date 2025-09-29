from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Mapping, Tuple, Union

from dotenv import load_dotenv

from app.database.read_db import read_db, read_to_list_index
from app.database.write_db import update_pallet_packing_list, write_db
from app.printer_connection.zpl_printer_logic import label_printer_connection
from app.static_json_readers import (
    get_all_pallet_label_zpl,
    get_pallet_label_zpl,
    validate_fn_usage,
)
from app.zpl.pallet_label_zpl_logic import (
    create_combined_pallet_label_data,
    create_pallet_label_zpl,
)

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
        print(pallet_label_zpl)
        # response = label_printer_connection(
        #     pallet_label_zpl, printer["ip"], printer["port"]
        # )
        # return response
        return pallet_label_zpl

    except Exception as ex:
        print("Label could not be created due to: \n", ex)


def upload_internal_label_structures_to_printers(
    printers: List[Dict[str, Union[str, int]]],
    *,
    dry_run: bool = True,
) -> str:
    """
    Compile ALL pallet label structures into one ZPL bundle and upload to each printer.

    Args:
        printers: list of {"ip": "...", "port": 9100}
        dry_run:  if True, print the ZPL bundle and return it without sending

    Returns:
        The compiled ZPL bundle (if dry_run), otherwise newline-joined printer responses.
    """
    try:
        # Build one ZPL stream containing ALL pallet structures (validates each)
        zpl = get_all_pallet_label_zpl(validate=True)

        if dry_run:
            print("--- DRY RUN: PALLET STRUCTURES ZPL BUNDLE ---")
            print(zpl)
            print("--- END DRY RUN ---")
            return zpl

        responses: List[str] = []
        for p in printers:
            ip = str(p["ip"])
            port = int(p["port"])
            try:
                resp = label_printer_connection(zpl, ip, port)
                print(f"synced to printer {ip}:{port}")
                responses.append(str(resp))
            except Exception as e:
                msg = f"ERROR syncing to {ip}:{port} -> {e}"
                print(msg)
                responses.append(msg)

        return "\n".join(responses)

    except Exception as ex:
        print("Pallet label structures could not be uploaded due to:\n", ex)
        return f"Error: {ex}"
