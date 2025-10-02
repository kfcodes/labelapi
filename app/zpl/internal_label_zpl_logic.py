def create_id_with_description(
    label_structure_name: str,
    product_id: str | int,
    product_description: str,
    quantity: int,
) -> str:
    return (
        "^XA\n"
        f"^XFE:{label_structure_name}.ZPL^FS\n"
        f"^PQ{quantity}^FS\n"
        f"^FN1^FD{product_id}^FS\n"
        f"^FN2^FD{product_description}^FS\n"
        "^XZ"
    )


def create_blend_label_zpl(
    label_structure_name: str, blend_id: str | int, allergens: str
) -> str:
    return (
        "^XA\n"
        f"^XFE:{label_structure_name}.ZPL^FS\n"
        f"^FN1^FD{blend_id}^FS\n"
        f"^FN2^FD{allergens}^FS\n"
        "^XZ"
    )


def create_blank_label_zpl(label_structure_name: str) -> str:
    return f"^XA^XFE:{label_structure_name}.ZPL^FS^XZ"
