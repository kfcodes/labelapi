def create_blend_label_zpl(
    label_structure_name: str, blend_id: str | int, allergens: str
) -> str:
    """
    Minimal internal label: references a stored template and fills a couple of fields.
    Adjust ^FN numbers to match your template if needed.
    """
    return (
        "^XA\n"
        f"^XFE:{label_structure_name}.ZPL^FS\n"
        f"^FN1^FD{blend_id}^FS\n"
        f"^FN2^FD{allergens}^FS\n"
        "^XZ"
    )
