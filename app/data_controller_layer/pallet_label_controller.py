import os

from dotenv import load_dotenv

from db_access_layer.read_db import *
from db_access_layer.write_db import update_pallet_packing_list
from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import *
from external_module_controller_layer.zpl_logic.pallet_label_zpl_logic import *

load_dotenv("env/pallet_label.env")


async def main_pallet_label_function(location, printer, pallet_id):
    try:
        # get the label summary information and type id from the database
        label_summary_info = read_db(
            str(f"{os.getenv('PALLETSUMMARY')}").format(int(pallet_id))
        )
        label_summary_info = label_summary_info[0]
        # label_type_info = read_to_list_index(str(f"{os.getenv('PALLETLABELTYPE')}").format(int(pallet_id)))
        label_type_info = read_db(str(f"{os.getenv('PALLETLABELTYPE')}"))
        label_structure_name = f"{label_type_info[0]['pallet_label_name']}"
        # setting the label structure statically for now
        label_structure_name = "PALSTD1"

        # blank label with pallet summary
        if int(label_type_info[0]["pallet_label_id"]) == 2:
            return
        # standard label with pallet contents containing product sku codes
        if int(label_type_info[0]["pallet_label_id"]) == 3:
            extra_info = standard_pallet_label_with_product_skus_extra_information(
                pallet_id
            )
        # standard label structure with the pallet contents on the label
        else:
            extra_info = standard_pallet_label_extra_information(pallet_id)

        # create the zpl string with the pallet information
        pallet_label_zpl = create_pallet_label_zpl(
            label_structure_name, label_summary_info, extra_info
        )
        print(pallet_label_zpl)
        # send the zpl string with the printer info to the print function
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )

        # update the pallet in the database to add it to packing list
        update_pallet_packing_list(pallet_id, location)
        return response
    except Exception as ex:
        print("Pallet label could not be created due to: \n", ex)


async def print_blank_pallet_labels(printer):
    try:
        label_structure_name = "PALBLNK"
        pallet_label_zpl = create_pallet_label_zpl(label_structure_name)
        response = label_printer_connection(
            pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)


async def generate_and_print_combo_label(printer, pallet_id, height, pallet_list):
    try:
        # Write the update to the DB
        update_pallets_response = read_db(str(os.getenv('COMBINEPALLETDATA')).format(pallet_id, height, pallet_list))
        print(update_pallets_response)

        # Format ID's for the pallets being combined
        ids = str(pallet_list)
        ids = ids.replace("(","")
        ids = ids.replace(")","")
        ids = ids.replace("'","")

        # Get the combined pallet details from the DB
        combined_pallet_data = read_to_list_index(str(os.getenv('GETCOMBINEDPALLETDATA')).format(pallet_id))
        combo_pallet_label_zpl = create_combined_pallet_label_data(combined_pallet_data[0], ids)

        response = label_printer_connection(
            combo_pallet_label_zpl, printer["ip"], printer["port"]
        )
        return response
    except Exception as ex:
        print("Data could not be processed: \n", ex)



# Supplementary functions
def standard_pallet_label_extra_information(pallet_id):
    # get the pallet item information from DB
    pallet_contents = read_db(
        f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}"
    )
    pallet_contents = tuple(pallet_contents.values())
    return pallet_contents


def standard_pallet_label_with_product_skus_extra_information(pallet_id):
    # get the pallet item information from DB
    pallet_contents = read_db(
        f"{os.getenv('GETPRODUCTSONPALLET1')} {int(pallet_id)} {os.getenv('GETPRODUCTSONPALLET2')}"
    )
    pallet_contents = tuple(pallet_contents.values())
    return pallet_contents


async def upload_pallet_label_data_to_printers(printers):
    try:
        stored_label_structures = str(f"{os.getenv('PALLETLABELSTRUCTURES')}")
        response = ""
        for printer in printers:
            printer_ip = printer["ip"]
            printer_port = printer["port"]
            printer_response = label_printer_connection(
                stored_label_structures, printer_ip, printer_port
            )
            response += f"{printer_response}\n\n"
        return response
    except Exception as ex:
        print("Pallet label structure could not be uploaded due to: \n", ex)
