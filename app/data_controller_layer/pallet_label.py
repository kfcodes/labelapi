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
from physical_layer.data_access_layer.write_database_functions import update_pallet

import os
from dotenv import load_dotenv
load_dotenv(".env")

async def print_blank_pallet_label():
    try:
        label_outline = create_blank_label_outline()
        response = print_large_label(label_outline)
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)

async def print_combined_pallet_label(data):
    try:
        label_info = str(data["label_info"])
        response = print_large_label(label_info)
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)

async def print_pallet_label(id):
    try:
        label_info_string = str(f"{os.getenv('PALLETLABELPART1')}")
        label_info = read_to_list_index(label_info_string.format(int(id),int(id)))
        print("Printing Pallet Label", label_info)
        print("label_info", label_info)
        outline = create_pallet_label_outline()
        pallet_products = read_to_list_index(f"{os.getenv('GETPRODUCTSONPALLET1')} {int(id)} {os.getenv('GETPRODUCTSONPALLET2')}")
        products = add_products_to_label(pallet_products)
        body = create_pallet_label_data(label_info[0])
        print(body)
        label_data = outline + products + body
        print(label_data)
        update_pallet(id);
        response = print_large_label(label_data)
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)
