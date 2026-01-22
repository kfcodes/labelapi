from typing import Optional


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
        f"^FN3^FD{blend_id}^FS\n"
        f"^FN4^FD{allergens}^FS\n"
        "^XZ"
    )


def create_blank_label_zpl(label_structure_name: str) -> str:
    return f"^XA^XFE:{label_structure_name}.ZPL^FS^XZ"


def create_goodsin_label_zpl(
    label_structure_name: str,
    *,
    product_id: str,
    intake_date: str,
    order_no: Optional[int],
    weight_kg: float,
    batch_code: str,
    labels_requested: Optional[int] = None,
    product_description: str,
    barcode: str,
) -> str:
    order_no_str = "" if order_no is None else str(order_no)
    labels_requested_str = "" if labels_requested is None else str(labels_requested)
    return (
        "^XA\n"
        f"^XFE:{label_structure_name}.ZPL^FS\n"
        f"^FN1^FD{product_id}^FS\n"
        f"^FN2^FD{product_description}^FS\n"
        f"^FN5^FD{intake_date}^FS\n"
        f"^FN6^FD{order_no_str}^FS\n"
        f"^FN7^FD{weight_kg}^FS\n"
        f"^FN8^FD{batch_code}^FS\n"
        f"^FN9^FD{barcode}^FS\n"
        "^XZ"
    )
