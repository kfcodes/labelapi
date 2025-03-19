import os
from dotenv import load_dotenv
load_dotenv(".env")

def create_pallet_label_zpl(label_type, label_summary_info, extra_info):
    try:
        if extra_info != None:
            format_extras = add_products_to_label(extra_info)
        else:
            format_extras = ""

        # get pallet structure name then apply the applicable variables
        zpl = f""" ^XA
                    ^XFE:{label_type}.ZPL^FS
                    ^FN1^FD{label_summary_info['pallet_id']}^FS
                    ^FN2^FD{int(label_summary_info['pallet_quantity'])}^FS
                    ^FN3^FD{label_summary_info['gross_weight']}^FS
                    ^FN4^FD{label_summary_info['pallet_dimensions']}^FS
                    {format_extras}
                ^XZ"""

        # then make the label string with the XA and XZ commands
        return(zpl)
    except Exception as ex:
        print("Data could not be processed: \n", ex)


def add_products_to_label(pallet_products):
    try:
        # initialising zpl to an empty string
        zpl = ""

        # if the pallet has more than 6 items apply "mixed pallet" value to label
        if((len(pallet_products))>7):
            zpl += f"""
                    ^FO350,420
                    ^A0,22
                    ^FDMIXED PALLET
                    ^FS
                    \n
                    """
        # if less than 6 distict items apply the pallet item information to the label
        else:
            key = 0;
            for product in pallet_products:
                position = 0
                if(key == 0):
                    position = 410
                    print(product)
                    key += 1
                elif(key == 1):
                    position = 380
                    print(product)
                    key += 1
                elif(key == 2):
                    position = 350
                    key += 1
                elif(key == 3):
                    position = 320
                    key += 1
                elif(key == 4):
                    position = 290
                    key += 1
                elif(key == 5):
                    position = 260
                    key += 1
                elif(key == 6):
                    position = 230
                    key += 1

                # each iteration adds the value to the label information
                zpl += f"""
                        ^FO{position},420
                        ^A0,22
                        ^FD{int(product['total'])}
                        ^FS
                        ^FO{position},480^A0,22
                        ^FD{product['product_description']}
                        ^FS\n
                    """
            # apply new line at the end of the zpl string after the loop
            zpl += f"\n"

        # return the full zpl string to the calling function
        return(zpl)

    except Exception as ex:
        print("Data could not be processed: \n", ex)

