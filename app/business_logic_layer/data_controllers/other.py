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

async def get_label_info(id):
    try:
        label_info_list = [];
        label_info = get_label_data(f"{os.getenv('GETLABELINFO')}'{id}'");
        label_info_list.append(label_info[0]);
        return label_info_list;
    except Exception as ex:
        print("Data could not be processed: \n", ex)

async def print_this_label(qty):
    try:
        print("data_layer")
        # label_outline = type_2_label.create_this_label(qty)
        label_outline = type_4_label.create_this_label_2(qty)
        print("print_label_data")
        print(label_outline)
        # response = print_small_label(label_outline)
        response = print_large_label(label_outline)
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)

async def print_specific_label_now():
    try:
        label_outline = f"""
        ^XA
        ^CF0,80
        TEST
        ^XZ"""
        response = print_specific_label(label_outline)
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)

# THIS IS THE FUNCTION TO PRINT THE NEW PRODUCT LABELS
async def print_specific_label_now_2(id):
    try:
        label_info = read_to_list_index(f"{os.getenv('TESTNEWLABEL')}'{id}'")
        label_outline = label_type_5.create_large_product_label_2(label_info[0])
        print(label_outline)
        response = print_specific_label(label_outline)
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)
