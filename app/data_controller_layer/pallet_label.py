from physical_layer.data_access_layer.read_database_functions import get_label_data, read_to_list_index
from business_logic_layer.external_module_controllers.zpl_logic.product_box_logic.small_type_1_box_label import create_small_label_data,  create_small_label_outline
from business_logic_layer.external_module_controllers.zpl_logic.pallet_logic.generic_pallet_label import create_pallet_label_outline, create_pallet_label_data, add_products_to_label
from business_logic_layer.external_module_controllers.zpl_logic.internal_logic.internal_pallet_label import create_blank_label_outline
from business_logic_layer.external_module_controllers.print_logic.print_zpl import print_small_label, print_large_label, print_specific_label
from physical_layer.data_access_layer.write_database_functions import update_pallet

import os
from dotenv import load_dotenv
load_dotenv(".env")

async def print_pallet_label(pallet_id, printer_id ):
    try:
        # setting the printer variables if no printer is stated print on 3rd printer
        if printer_id == "s":
            printer_address = os.getenv("BIGLABELID1")
            printer_port = int(os.getenv("BIGLABELPORT1"))
        if printer_id == "c":
            printer_address = os.getenv("BIGLABELID2")
            printer_port = int(os.getenv("BIGLABELPORT2"))
        else:
            printer_address = os.getenv("BIGLABELID3")
            printer_port = int(os.getenv("BIGLABELPORT3"))

        # get the label structure name from the database
        label_structure_id = read_to_list_index(label_info_string.format(int(pallet_id),int(pallet_id)))
        # if label_structure_id != None:
            # get pallet label summary information from DB
        label_summary_info = str(f"{os.getenv('PALLETLABELPART1')}")
        # else:
          #   return "could not do";


        # Standard label structure
        if label_structure_id == 1:
            pallet_label = standard_pallet_label_structure()

        # blank label with pallet summary
        if label_structure_id == 2:
            pallet_label = blank_pallet_label_structure()

        # Standard label with product SKU codes
        if label_structure_id == 3:
            pallet_label = standar_pallet_label_with_product_skus_structure()

        # default label format
        else:
            # get the pallet item information from DB
            pallet_contents = read_to_list_index(f"{os.getenv('GETPRODUCTSONPALLET1')} {int(id)} {os.getenv('GETPRODUCTSONPALLET2')}")
            formatted_pallet_contents = format_pallet_contents(pallet_contents)

            pallet_label_zpl = create_pallet_label_zpl(label_summary_info, formatted_pallet_contents)
            response = print_zpl_label(pallet_label_zpl, printer_address, printer_port)

        """
        update_pallet(id);
        """
        return response

    except Exception as ex:
        print("Pallet label could not be created due to: \n", ex)

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

