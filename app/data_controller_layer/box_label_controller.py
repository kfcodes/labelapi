from db_access_layer.read_db import read_db
from external_module_controller_layer.zpl_logic.pallet_label import create_box_label_zpl
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import label_printer_connection

import os
from dotenv import load_dotenv
load_dotenv(".env")

async def print_large_product_label(id, quantity, quantity_in_a_box, exp):
    try:
        # Get the unique information from the db
        unique_box_detals = read_db(f"{os.getenv('PRODUCTIONLABELINFO')}{id}")
        unique_box_detals = unique_box_detals[0]

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

            # modify the unique_box_detals to abstract the data being applied to the label

        label_data_string = create_box_label_string(label_info, quantity, quantity_in_a_box, exp)
        response = label_printer_connection(label_data_string, big_printer_id, big_printer_com)

        return response;

    except Exception as ex:
        print("Data could not be processed: \n", ex)
