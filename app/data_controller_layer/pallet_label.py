from db_access_layer.read_database_functions import read_to_list_index
from external_module_controller_layer.zpl.pallet_label import create_pallet_label_zpl
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import label_printer_connection
# from physical_layer.data_access_layer.write_database_functions import update_pallet

import os
from dotenv import load_dotenv
load_dotenv(".env")

async def upload_pallet_label_data_to_printers():
    try:
        # load the label structures into variable
        label_structures = str(f"{os.getenv('PALLETLABELSTRUCTURES')}")

        # Loop over all printers and send the label information
        # for each printer in printers;
        #     send the label_structure

        response = ""
        # for now just hardocoding the labelprinters
        """
            printer_address = os.getenv("BIGLABELID1")
            printer_port = int(os.getenv("BIGLABELPORT1"))
            printer_response = label_printer_connection(pallet_label_zpl, printer_address, printer_port)
            response += printer_response;
            printer_address = os.getenv("BIGLABELID2")
            printer_port = int(os.getenv("BIGLABELPORT2"))
            printer_response = label_printer_connection(pallet_label_zpl, printer_address, printer_port)
            response += printer_response;
        """

        printer_address = os.getenv("BIGLABELID3")
        printer_port = int(os.getenv("BIGLABELPORT3"))
        printer_response = label_printer_connection(label_structures, printer_address, printer_port)
        # response += printer_response;
        response = printer_response;
        return response

    except Exception as ex:
        print("Pallet label structure could not be uploaded due to: \n", ex)

async def format_and_print_pallet_label(pallet_id, printer_id):
    try:
        # setting the printer variables if no printer is stated use default/3rd printer
        if printer_id == "s":
            printer_address = os.getenv("BIGLABELID1")
            printer_port = int(os.getenv("BIGLABELPORT1"))
        if printer_id == "c":
            printer_address = os.getenv("BIGLABELID2")
            printer_port = int(os.getenv("BIGLABELPORT2"))
        else:
            printer_address = os.getenv("BIGLABELID3")
            printer_port = int(os.getenv("BIGLABELPORT3"))

        # get the label summary information and type id from the database
        label_summary_info = read_to_list_index(str(f"{os.getenv('PALLETSUMMARY')}").format(int(pallet_id)))
        label_summary_info = label_summary_info[0]
        # print(label_summary_info)

        # label_type_id = read_to_list_index(str(f"{os.getenv('PALLETLABELTYPE')}").format(int(pallet_id)))
        label_type_id = read_to_list_index(str(f"{os.getenv('PALLETLABELTYPE')}"))
        label_type_id = f"{label_type_id[0]['pallet_label_name']}"
        # print(label_type_id)
        label_type_id = "PALSTD1"

        # blank label with pallet summary
        if label_type_id == 2:
            return;
        # standard label with pallet contents containing product sku codes
        if label_type_id == 3:
            extra_info = standard_pallet_label_with_product_skus_extra_information(pallet_id)
        # standard label structure with the pallet contents on the label
        else:
            extra_info = standard_pallet_label_extra_information(pallet_id)

        # print(len(extra_info))
        # create the zpl string with the pallet information
        pallet_label_zpl = create_pallet_label_zpl(label_type_id, label_summary_info, extra_info)
        # print(pallet_label_zpl)

        # send the zpl string with the printer info to the print function
        response = label_printer_connection(pallet_label_zpl, printer_address, printer_port)

        """
        update the pallet in the database to add it to packing list
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

# Supplementary functions
def standard_pallet_label_extra_information(pallet_id):
    # get the pallet item information from DB
    pallet_contents = read_to_list_index(f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}")
    pallet_contents = tuple(pallet_contents.values())
    return pallet_contents;

def standard_pallet_label_with_product_skus_extra_information(pallet_id):
    # get the pallet item information from DB
    pallet_contents = read_to_list_index(f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}")
    return [pallet_contents];
