import json

from external_module_controller_layer.printer_connection_logic.zpl_printer_logic import *
from external_module_controller_layer.zpl_logic.internal_label_zpl_logic import (
    create_blend_label_zpl,
)


# async def blend_label_function(site,printer, body):
async def blend_label_function(body):
    try:
        label_structure_name = "INTBLND"
        pallet_label_zpl = create_blend_label_zpl(
            label_structure_name, body["blend_id"], body["allergens"]
        )
        print(pallet_label_zpl)
        # response = label_printer_connection(
        #     pallet_label_zpl, printer["ip"], printer["port"]
        # )
        # return response
        return pallet_label_zpl

    except Exception as ex:
        print("Label could not be created due to: \n", ex)
