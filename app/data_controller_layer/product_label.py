from physical_layer.data_access_layer.read_database_functions import get_label_data, read_to_list_index
from business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.small_type_1_box_label import create_small_label_data,  create_small_label_outline
from business_logic_layer.external_module_controllers.zpl_logic.pallet_logic.generic_pallet_label import create_pallet_label_outline, create_pallet_label_data, add_products_to_label
from business_logic_layer.external_module_controllers.zpl_logic.internal_logic.internal_pallet_label import create_blank_label_outline
from business_logic_layer.external_module_controllers.print_logic.print_zpl import print_small_label, print_large_label, print_specific_label
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.large_type_1_box_label as label_type_1
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.large_type_2_box_label as label_type_2
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.large_type_3_box_label as label_type_3
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.large_type_4_box_label as label_type_4
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.large_type_5_box_label as label_type_5
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.large_type_6_box_label as label_type_6
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.small_type_2_box_label as type_2_label
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.small_type_3_box_label as type_3_label
import business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.small_type_4_box_label as type_4_label
import pprint
from physical_layer.data_access_layer.write_database_functions import update_pallet

import os
from dotenv import load_dotenv
load_dotenv(".env")

async def print_large_product_label(id, quantity, quantity_in_a_box, exp):
    try:
        label_info = read_to_list_index(f"{os.getenv('PRODUCTIONLABELINFO')}{id}")
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
