import os
from dotenv import load_dotenv
load_dotenv(".env")

def create_box_label_zpl(label_data):
    try:
        # Destructure the label data into the required variables
        name = {label_data['label_structure_name']}
        item = {label_data['desctription']}
        sku = {label_data['sku']}
        lot = {label_data['lot']}
        bn = {label_data['batch']}
        bbe = {label_data['bbe']}
        bc = {label_data['box_barcode']}
        qty = {label_data['quantity']}
        exp = {label_data['exp']}


        # if else statement to determin the label structure
        # get pallet structure name then apply the applicable variables
        zpl = f"""
           ^XA
           ^XFE:{label_type}.ZPL^FS
           {pallet_information}
           ^XZ"""

        # then make the label string with the XA and XZ commands
        return(zpl)
    except Exception as ex:
        print("Data could not be processed: \n", ex)
