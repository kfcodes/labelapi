import os
import re
from pathlib import Path
from typing import Dict, Union

from dotenv import load_dotenv

from data_controller_layer.json_controller import load_box_label_variables
from db_access_layer.read_db import read_db
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import \
    label_printer_connection
from external_module_controller_layer.zpl_logic.box_label_zpl_logic import \
    create_box_label_zpl

load_dotenv("env/box_label.env")


async def main_print_box_label_function(unique_id, quantity, printer):
    try:
        # Get the unique information from the db including the label structure name
        box_label_info = read_db(f"{os.getenv('PRODUCTIONLABELINFO')}{unique_id}")
        box_label_info = box_label_info[0]
        # This function determines which printer to use big/small and label structure
        zpl_string = create_box_label_zpl(box_label_info, quantity)
        # Determine label size and select large or small printer
        if int(box_label_info["label_size"]) == 1:
            response = label_printer_connection(
                zpl_string, printer["large"]["ip"], printer["large"]["port"]
            )
        else:
            response = label_printer_connection(
                zpl_string, printer["small"]["ip"], printer["small"]["port"]
            )
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)


async def upload_box_label_structures_to_printers(printers):
    try:
        # Load and compile templates
        template_zpl = load_label_template_from_env(print_output=True)
        box_label_variables = load_box_label_variables()
        compiled_template_zpl = apply_zpl_placeholders(
            template_zpl, box_label_variables, print_output=True
        )

        # TEMP: return compiled for preview
        lines = re.findall(r"[\^~][A-Z0-9]+[^~\^]*", compiled_template_zpl)
        for line in lines:
            print(line)
        return compiled_template_zpl

        # response = ""
        # for printer in printers:
        #     printer_ip = printer["ip"]
        #     printer_port = printer["port"]
        #     printer_response = label_printer_connection(compiled_template_zpl, printer_ip, printer_port)
        #     response += f"{printer_response}\n\r"
        # return response

    except Exception as ex:
        print("Box label structure could not be uploaded due to:\n", ex)
        return f"Error: {ex}"


def load_label_template_from_env(print_output: bool = False) -> str:
    """
    Loads the raw ZPL label template string from the BOXLABELSTRUCTURES environment variable.

    Returns:
        str: ZPL template string directly from the environment.
    """
    template_str = os.getenv("BOXLABELSTRUCTURES")

    if not template_str:
        raise ValueError(
            "BOXLABELSTRUCTURES environment variable is not set or is empty."
        )

    if print_output:
        print("[Template Loaded from ENV VAR]")

    return template_str


def apply_zpl_placeholders(
    template_str: str, field_map: Dict[str, Union[str, int]], print_output: bool = False
) -> str:
    """
    Replaces {placeholders} in the template using provided field_map.
    """
    updated_template = template_str
    unmatched = []

    placeholders = re.findall(r"\{(.*?)\}", template_str)

    for key in placeholders:
        if key in field_map:
            replacement = str(field_map[key])
            updated_template = updated_template.replace(f"{{{key}}}", replacement)
            if print_output:
                print(f"Replaced {{{key}}} → {replacement}")
        else:
            unmatched.append(key)

    if unmatched:
        raise ValueError(f"Unmatched placeholders in template: {unmatched}")

    return updated_template
