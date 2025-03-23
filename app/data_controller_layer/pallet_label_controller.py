from db_access_layer.read_db import read_db
from external_module_controller_layer.zpl_logic.pallet_label_zpl_logic import create_pallet_label_zpl
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import label_printer_connection
from db_access_layer.write_db import update_pallet_packing_list

import os
from dotenv import load_dotenv
load_dotenv("env/pallet_label.env")

async def main_pallet_label_function(printer_id, pallet_id):
    try:
        # setting the printer variables if no printer is stated use default/3rd printer
        if printer_id == "c":
            printer_address = os.getenv("L1CID")
            printer_port = int(os.getenv("L1CP"))
        elif printer_id == "s":
            printer_address = os.getenv("L1SID")
            printer_port = int(os.getenv("L1SP"))
        else:
            print("using else printer")
            printer_address = os.getenv("L2SID")
            printer_port = int(os.getenv("L2SP"))

        # get the label summary information and type id from the database
        label_summary_info = read_db(str(f"{os.getenv('PALLETSUMMARY')}").format(int(pallet_id)))
        label_summary_info = label_summary_info[0]

        # label_type_info = read_to_list_index(str(f"{os.getenv('PALLETLABELTYPE')}").format(int(pallet_id)))
        label_type_info = read_db(str(f"{os.getenv('PALLETLABELTYPE')}"))
        label_structure_name = f"{label_type_info[0]['pallet_label_name']}"
        # setting the label structure statically for now
        label_structure_name = "PALSTD1"

        # blank label with pallet summary
        if int(label_type_info[0]['pallet_label_id']) == 2:
            return;
        # standard label with pallet contents containing product sku codes
        if int(label_type_info[0]['pallet_label_id']) == 3:
            extra_info = standard_pallet_label_with_product_skus_extra_information(pallet_id)
        # standard label structure with the pallet contents on the label
        else:
            extra_info = standard_pallet_label_extra_information(pallet_id)

        # create the zpl string with the pallet information
        pallet_label_zpl = create_pallet_label_zpl(label_structure_name, label_summary_info, extra_info)

        # send the zpl string with the printer info to the print function
        response = label_printer_connection(pallet_label_zpl, printer_address, printer_port)

        # update the pallet in the database to add it to packing list
        update_pallet_packing_list(pallet_id);

        return response

    except Exception as ex:
        print("Pallet label could not be created due to: \n", ex)

async def print_blank_pallet_labels(printer_id):
    try:
        # setting the printer variables if no printer is stated use default/3rd printer
        if printer_id == "c":
            printer_address = os.getenv("L1CID")
            printer_port = int(os.getenv("L1CP"))
        elif printer_id == "s":
            printer_address = os.getenv("L1SID")
            printer_port = int(os.getenv("L1SP"))
        else:
            print("using else printer")
            printer_address = os.getenv("L2SID")
            printer_port = int(os.getenv("L2SP"))

        label_structure_name = "PALBLNK"

        label_zpl = create_pallet_label_zpl(label_structure_name)
        response = label_printer_connection(label_zpl, printer_address, printer_port)
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)

async def print_combined_pallet_label(data, printer_id):
    try:
        # setting the printer variables if no printer is stated use default/3rd printer
        if printer_id == "c":
            printer_address = os.getenv("L1CID")
            printer_port = int(os.getenv("L1CP"))
        elif printer_id == "s":
            printer_address = os.getenv("L1SID")
            printer_port = int(os.getenv("L1SP"))
        else:
            print("using else printer")
            printer_address = os.getenv("L2SID")
            printer_port = int(os.getenv("L2SP"))

        label_info = str(data["label_info"])
        response = print_large_label(label_info)
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)

# Supplementary functions
def standard_pallet_label_extra_information(pallet_id):
    # get the pallet item information from DB
    pallet_contents = read_db(f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}")
    pallet_contents = tuple(pallet_contents.values())
    return pallet_contents;

def standard_pallet_label_with_product_skus_extra_information(pallet_id):
    # get the pallet item information from DB
    pallet_contents = read_db(f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}")
    pallet_contents = tuple(pallet_contents.values())

async def upload_pallet_label_data_to_printers():
    try:
        # load the label structures into variable
        label_structures = str(f"{os.getenv('PALLETLABELSTRUCTURES')}")

        # Loop over all printers and send the label information
        # for each printer in printers;
        #     send the label_structure

        response = ""
        # for now just hardocoding the labelprinters
        printer_address = os.getenv("L1SID")
        printer_port = int(os.getenv("L1SP"))
        printer_response = label_printer_connection(label_structures, printer_address, printer_port)
        response += printer_response;
        printer_address = os.getenv("L1CID")
        printer_port = int(os.getenv("L1CP"))
        printer_response = label_printer_connection(label_structures, printer_address, printer_port)
        response += printer_response;
        printer_address = os.getenv("L2SID")
        printer_port = int(os.getenv("L2SP"))
        printer_response = label_printer_connection(label_structures, printer_address, printer_port)
        response += printer_response;

        return response

    except Exception as ex:
        print("Pallet label structure could not be uploaded due to: \n", ex)
    return pallet_contents;
