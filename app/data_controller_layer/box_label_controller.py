from db_access_layer.read_db import read_db
from external_module_controller_layer.zpl_logic.box_label_zpl_logic import create_box_label_zpl
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import label_printer_connection
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import *

import os
from dotenv import load_dotenv
load_dotenv("env/box_label.env")

async def main_print_box_label_function(unique_id, quantity, printer):
    try:
        # Get the unique information from the db including the label structure name
        box_label_info = box_label_info[0] = read_db(f"{os.getenv('PRODUCTIONLABELINFO')}{unique_id}")
        # This function determines which printer to use big/small and label structure
        zpl_string = create_box_label_zpl(box_label_info, quantity)
        # Determine label size and select large or small printer
        if int(box_label_info['label_size']) == 1:
            response = label_printer_connection(zpl_string, printer['large']['ip'] , printer['large']['port'] )
        else:
            response = label_printer_connection(zpl_string, printer['small']['ip'] , printer['small']['port'] )
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)

async def upload_box_label_structures_to_printers(printers):
    try:
        # load the label structures into variable
        box_label_structures = str(f"{os.getenv('BOXLABELSTRUCTURES')}")
        response = ""
        for printer in printers:
            printer_ip = printer["ip"]
            printer_port = printer["port"]
            printer_response = label_printer_connection(box_label_structures, printer_ip, printer_port)
            response += f"{printer_response}\n\r"
        return response
    except Exception as ex:
        print("Pallet label structure could not be uploaded due to: \n", ex)
