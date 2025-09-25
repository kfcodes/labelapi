from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Mapping, Tuple, Union

from app.database.read_db import read_db, read_to_list_index
from app.database.write_db import update_pallet_packing_list, write_db
from app.printer_connection.zpl_printer_logic import label_printer_connection
from app.static_json_readers import get_pallet_label_zpl, validate_fn_usage
from app.zpl.pallet_label_zpl_logic import (
    create_combined_pallet_label_data,
    create_pallet_label_zpl,
)
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]  # -> app/
load_dotenv(BASE_DIR / "env" / "label_variables.env")


async def main_pallet_label_function(location, printer, pallet_id):
    """
    Build a pallet label ZPL string using DB data and send it to a specific printer.
    `printer` is a dict like {"ip": "...", "port": 9100}.
    """
    try:
        label_summary_info = read_db(
            str(f"{os.getenv('PALLETSUMMARY')}").format(int(pallet_id))
        )[0]
        label_type_info = read_db(str(f"{os.getenv('PALLETLABELTYPE')}"))
        label_structure_name = "PALSTD1"

        if int(label_type_info[0]["pallet_label_id"]) == 2:
            return  # blank summary only — nothing to print per original logic
        elif int(label_type_info[0]["pallet_label_id"]) == 3:
            extra_info = standard_pallet_label_with_product_skus_extra_information(
                pallet_id
            )
        else:
            extra_info = standard_pallet_label_extra_information(pallet_id)

        pallet_label_zpl = create_pallet_label_zpl(
            label_structure_name, label_summary_info, extra_info
        )
        print(pallet_label_zpl)

        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )

        # update_pallet_packing_list(pallet_id, location)
        return response
    except Exception as ex:
        print("Pallet label could not be created due to: \n", ex)


async def print_blank_pallet_labels(printer):
    """Print a blank pallet label template (PALBLNK)."""
    try:
        label_structure_name = "PALBLNK"
        pallet_label_zpl = create_pallet_label_zpl(label_structure_name)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)


async def generate_and_print_combo_label(printer, pallet_id, height, pallet_list):
    """
    Generate & print a combined (combo) pallet label.
    """
    try:
        # Write the update to the DB
        update_pallets_response = write_db(
            str(os.getenv("COMBINEPALLETDATA")).format(pallet_id, height, pallet_list)
        )
        print("update_pallets_response")
        print(update_pallets_response)

        # Format IDs for the pallets being combined
        ids = str(pallet_list).replace("(", "").replace(")", "").replace("'", "")
        print(ids)

        # Get combined pallet details from the DB
        combined_pallet_data = read_to_list_index(
            str(os.getenv("GETCOMBINEDPALLETDATA")).format(pallet_id)
        )
        print(combined_pallet_data)
        combo_pallet_label_zpl = create_combined_pallet_label_data(
            combined_pallet_data[0], ids
        )

        response = label_printer_connection(
            combo_pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response

    except Exception as ex:
        print("Data could not be processed: \n", ex)


def standard_pallet_label_extra_information(pallet_id):
    # get the pallet item information from DB
    pallet_contents = read_db(
        f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}"
    )
    pallet_contents = tuple(pallet_contents.values())
    return pallet_contents


def standard_pallet_label_with_product_skus_extra_information(pallet_id):
    # get the pallet item information from DB
    pallet_contents = read_db(
        f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}"
    )
    pallet_contents = tuple(pallet_contents.values())
    return pallet_contents


def upload_pallet_label_data_to_printers(
    printers: List[Dict[str, Union[str, int]]],
    *,
    label_name: str = "PALSTD1",
    dry_run: bool = True,
) -> str:
    """
    Compile the pallet label structure (e.g., 'PALSTD1') and upload it to each printer.

    Args:
        printers: list of {"ip": "...", "port": 9100}
        label_name: key in PALLETLABELSTRUCTURES to upload
        dry_run: if True, only print the ZPL to console and return it

    Returns:
        The compiled ZPL string (if dry_run), otherwise newline-joined printer responses.
    """
    try:
        load_pallet_config()
        validate_fn_usage(label_name)

        zpl = get_pallet_label_zpl(label_name)

        if dry_run:
            print(f"--- DRY RUN UPLOAD PALLET STRUCTURE '{label_name}' ---")
            for line in zpl.splitlines():
                if line.strip():
                    print(line)
            print("--- END STRUCTURE ---")
            return zpl

        responses: List[str] = []
        for p in printers:
            ip = str(p["ip"])
            port = int(p["port"])
            resp = label_printer_connection(zpl, ip, port)
            responses.append(str(resp))
        return "\n".join(responses)
    except Exception as ex:
        print("Pallet label structure could not be uploaded due to: \n", ex)
        return f"Error: {ex}"
