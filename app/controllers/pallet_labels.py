from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple, Union

from dotenv import load_dotenv

from app.database.read_db import read_db, read_to_list_index
from app.database.write_db import update_pallet_packing_list, write_db
from app.printer_connection.zpl_printer_logic import label_printer_connection
from app.static_json_readers import get_all_pallet_label_zpl, get_pallet_label_zpl
from app.static_json_readers.pallet_json_readers import get_pallet_variables
from app.zpl.pallet_label_zpl_logic import create_pallet_label_zpl

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / "env" / "label_variables.env")


def make_pallet_label_payload(
    summary_row: Mapping[str, Any],
    *,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a payload whose keys match PALLETVARIABLES.
    Missing values default to "" (empty string) so the ZPL still prints cleanly.
    Use `overrides` to set/replace specific keys (e.g., combo_pallet_ids).
    """
    vars_map = get_pallet_variables()  # just to know the canonical key set
    base = {k: summary_row.get(k, "") for k in vars_map.keys()}
    if overrides:
        base.update(overrides)
    return base


async def print_blank_pallet_labels(printer):
    try:
        label_structure_name = "PALBLNK"
        zpl = create_pallet_label_zpl(label_structure_name, {})  # no values
        print(zpl)
        return label_printer_connection(zpl, printer["ip"], printer["port"])
    except Exception as ex:
        print("Data could not be processed:\n", ex)


async def main_pallet_label_function(location, printer, pallet_id):
    try:
        summary = read_db(str(f"{os.getenv('PALLETSUMMARY')}").format(int(pallet_id)))[
            0
        ]
        label_type_info = read_db(str(f"{os.getenv('PALLETLABELTYPE')}"))
        label_structure_name = "PALSTD1"  # or derive from label_type_info if needed

        if int(label_type_info[0]["pallet_label_id"]) == 2:
            return  # blank summary only
        elif int(label_type_info[0]["pallet_label_id"]) == 3:
            extra_info = standard_pallet_label_with_product_skus_extra_information(
                pallet_id
            )
        else:
            extra_info = standard_pallet_label_extra_information(pallet_id)

        payload = make_pallet_label_payload(summary)
        zpl = create_pallet_label_zpl(
            label_structure_name, payload, extra_info, copies=1
        )
        print(zpl)

        resp = label_printer_connection(zpl, printer["ip"], printer["port"])
        # update_pallet_packing_list(pallet_id, location)
        return resp
    except Exception as ex:
        print("Pallet label could not be created due to:\n", ex)


async def generate_and_print_combo_label(printer, pallet_id, height, pallet_list):
    try:
        write_db(
            str(os.getenv("COMBINEPALLETDATA")).format(pallet_id, height, pallet_list)
        )
        label_structure_name = "PALCOMBO"

        ids = str(pallet_list).replace("(", "").replace(")", "").replace("'", "")
        combined_rows = read_to_list_index(
            str(os.getenv("GETCOMBINEDPALLETDATA")).format(pallet_id)
        )
        summary = combined_rows[0] if combined_rows else {}

        payload = make_pallet_label_payload(
            summary, overrides={"combo_pallet_ids": ids}
        )
        zpl = create_pallet_label_zpl(
            label_structure_name, payload, extra_info=None, copies=1
        )
        print(zpl)

        return label_printer_connection(zpl, printer["ip"], printer["port"])
    except Exception as ex:
        print("Data could not be processed:\n", ex)


def standard_pallet_label_extra_information(pallet_id):
    pallet_contents = read_db(
        f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}"
    )
    pallet_contents = tuple(pallet_contents.values())
    return pallet_contents


def standard_pallet_label_with_product_skus_extra_information(pallet_id):
    pallet_contents = read_db(
        f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}"
    )
    pallet_contents = tuple(pallet_contents.values())
    return pallet_contents
