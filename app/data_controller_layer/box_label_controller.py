from db_access_layer.read_db import read_db
from external_module_controller_layer.zpl_logic.box_label_zpl_logic import create_box_label_zpl
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import label_printer_connection
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import *

import os
from dotenv import load_dotenv
load_dotenv("env/box_label.env")

async def main_print_box_label_function(product_id, quantity, printer_id):
    try:
        # Get the unique information from the db including the label structure name
        unique_box_detals = unique_box_detals[0] = read_db(f"{os.getenv('PRODUCTIONLABELINFO')}{product_id}")

        # Determine which printer group to use
        if printer_id == "c":
            big_printer_id = os.getenv("L1LCID")
            big_printer_com = int(os.getenv("L1LCP"))
            small_printer_id = os.getenv("L1SCID")
            small_printer_com = int(os.getenv("L1SCP"))
        elif printer_id == "s":
            big_printer_id = os.getenv("L1LSID")
            big_printer_com = int(os.getenv("L1LSP"))
            small_printer_id = os.getenv("L1SSID")
            small_printer_com = int(os.getenv("L1SSP"))
        else:
            print("using fallback printer")
            big_printer_id = os.getenv("L2LSID")
            big_printer_com = int(os.getenv("L2LSP"))
            small_printer_id = os.getenv("L2SSID")
            small_printer_com = int(os.getenv("L2SSP"))

        # This function determines which printer to use big/small and label structure
        label_data_string = create_box_label_zpl(unique_box_detals, quantity)

        if int(unique_box_detals['label_size']) == 1:
            response = label_printer_connection(label_data_string, big_printer_id, big_printer_com)
        else:
            response = label_printer_connection(label_data_string, small_printer_id, small_printer_com)

        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)



async def upload_box_label_structures_to_printers():
    try:
        # load the label structures into variable
        label_structures = str(f"{os.getenv('PALLETLABELSTRUCTURES')}")

        response = ""
        # for now just hardocoding the labelprinters
        printer_address = os.getenv("L1SID")
        printer_port = int(os.getenv("L1SP"))
            big_printer_id = os.getenv("L1LCID")
            big_printer_com = int(os.getenv("L1LCP"))
            printer_address = os.getenv("L1SCID")
            printer_port = int(os.getenv("L1SCP"))
        printer_response = label_printer_connection(label_structures, printer_address, printer_port)
        response += printer_response
        response += "\n"
        printer_address = os.getenv("L1CID")
        printer_port = int(os.getenv("L1CP"))
        printer_response = label_printer_connection(label_structures, printer_address, printer_port)
        response += printer_response
        response += "\n"
        address = os.getenv("L2SID")
        port = int(os.getenv("L2SP"))
        printer_response = label_printer_connection(label_structures, printer_address, printer_port)
        response += printer_response
        response += "\n"

        return response
    except Exception as ex:
        print("Pallet label structure could not be uploaded due to: \n", ex)
