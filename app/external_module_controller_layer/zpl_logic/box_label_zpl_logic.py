import os
from dotenv import load_dotenv
load_dotenv(".env")

def create_box_label_zpl(label_data, qty):
    try:
        # Destructure the label data into the required variables
       name = {label_data['label_structure_name']}
       item = {label_data['desctription']}
       sku = {label_data['sku']}
       bx_qty = {label_data['quantity']}
       bc = {label_data['box_barcode']}
       lot = {label_data['lot']}
       bn = {label_data['batch']}
       bbe = {label_data['bbe']}
       exp = {label_data['exp']}

        # if else statement to determin the label structure
        # get pallet structure name then apply the applicable variables
        zpl = f"""
           ^XA
           ^XFE:{name}.ZPL^FS
           ^PQ{qty},10,1,Y
            ^FN1^FD{item}^FS
            ^FN2^FD{sku}^FS
            ^FN3^FD{bx_qty}^FS
            ^FN4^FD{bc}^FS
            ^FN5^FD{lot}^FS
            ^FN6^FD{bn}^FS
            ^FN7^FD{bbe}^FS
            ^FN8^FD{exp}^FS
           ^XZ"""

        # then make the label string with the XA and XZ commands
        return(zpl)
    except Exception as ex:
        print("Data could not be processed: \n", ex)
