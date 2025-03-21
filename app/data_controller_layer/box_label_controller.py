from db_access_layer.read_db import read_db
from external_module_controller_layer.zpl_logic.pallet_label import create_box_label_zpl
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import label_printer_connection

import os
from dotenv import load_dotenv
load_dotenv(".env")

async def print_large_product_label(id, quantity, quantity_in_a_box, exp):
    try:
        label_info = read_db(f"{os.getenv('PRODUCTIONLABELINFO')}{id}")
        label_type = int(label_info[0][f'{os.getenv("LABELFIELD20")}'])
        label_info = label_info[0]

        if label_type == 1:
            outline = label_type_1.create_large_product_label_outline()
            body = label_type_1.create_large_product_label_data(label_info, quantity, quantity_in_a_box, exp)
            label_data = outline + body
            response = print_large_label(label_data)

        elif label_type == 2:
            outline = label_type_2.create_large_product_label_outline()
            body = label_type_2.create_large_product_label_data(label_info, quantity, quantity_in_a_box, exp)
            label_data = outline + body
            response = print_large_label(label_data)

        elif label_type == 3:
            outline = label_type_3.create_large_product_label_outline()
            body = label_type_3.create_large_product_label_data(label_info, quantity, quantity_in_a_box, exp)
            label_data = outline + body
            response = print_large_label(label_data)

        elif label_type == 4:
            outline = label_type_4.create_large_product_label_outline()
            body = label_type_4.create_large_product_label_data(label_info, quantity, quantity_in_a_box, exp)
            label_data = outline + body
            response = print_large_label(label_data)

        elif label_type == 6:
            body = label_type_6.create_large_product_label(label_info, quantity)
            pprint.pp(body)
            response = print_small_label(body)
        else:
            response = {"message" : "No label Data for this label"}

        return response

    except Exception as ex:
        print("Data could not be processed: \n", ex)
