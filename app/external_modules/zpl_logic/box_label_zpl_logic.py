from app.controller.json_controller import box_label_variables


def create_box_label_zpl(label_data: dict, qty: int, debug: bool = False) -> str:
    """
    Generate a ZPL string for a box label using the global mapping (box_label_variables).
    Assumes box_label_variables has been populated (e.g., via load_all_config_data()).
    """
    try:
        name = label_data.get("label_structure_name", "DEFAULT")

        zpl_lines = [
            "^XA",
            f"^XFE:{name}.ZPL^FS",  # Use stored template on printer
            f"^PQ{int(qty)},10,1,Y",  # Quantity & reprint behavior
        ]

        missing = []
        for field_name, fn_number_str in box_label_variables.items():
            fn = int(fn_number_str)
            value = label_data.get(field_name, "")
            if value == "" and debug:
                missing.append(field_name)
            zpl_lines.append(f"^FN{fn}^FD{value}^FS")

        zpl_lines.append("^XZ")

        if debug:
            if missing:
                print(f"[ZPL DEBUG] Missing values for fields: {missing}")
            print("[ZPL DEBUG] Generated ZPL:\n" + "\n".join(zpl_lines))

        return "\n".join(zpl_lines)
    except Exception as e:
        if debug:
            print(f"[ZPL ERROR] Failed to generate label: {e}")
        return ""
