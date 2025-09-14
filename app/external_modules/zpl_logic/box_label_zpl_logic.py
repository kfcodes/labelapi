import os

from dotenv import load_dotenv

load_dotenv(".env")
from data_controller_layer.json_controller import box_label_variables


def create_box_label_zpl(label_data: dict, qty: int, debug: bool = False) -> str:
    """
    Generates a ZPL string for a box label using a mapped set of field names (box_label_variables).

    Args:
        label_data (dict): Dictionary of label data (field_name: value)
        qty (int): Number of labels to print
        debug (bool): If True, logs missing fields and prints result

    Returns:
        str: Fully compiled ZPL label string
    """
    try:
        name = label_data.get("label_structure_name", "DEFAULT")

        # Start ZPL
        zpl_lines = [
            "^XA",
            f"^XFE:{name}.ZPL^FS",  # Template file reference
            f"^PQ{qty},10,1,Y",  # Quantity and print settings
        ]

        # Track missing fields if debugging
        missing_fields = []

        # Loop over field mappings
        for field_name, fn_number_str in box_label_variables.items():
            fn_number = int(fn_number_str)
            field_value = label_data.get(field_name, "")

            if field_value == "" and debug:
                missing_fields.append(field_name)

            zpl_lines.append(f"^FN{fn_number}^FD{field_value}^FS")

        zpl_lines.append("^XZ")

        if debug:
            if missing_fields:
                print(f"[ZPL DEBUG] Missing values for fields: {missing_fields}")
            print("[ZPL DEBUG] Generated ZPL:\n" + "\n".join(zpl_lines))

        return "\n".join(zpl_lines)

    except Exception as e:
        error_msg = f"[ZPL ERROR] Failed to generate label: {e}"
        if debug:
            print(error_msg)
        return ""
