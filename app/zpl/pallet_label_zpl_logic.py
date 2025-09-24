def create_pallet_label_zpl(
    label_type: str,
    label_summary_info: dict | None = None,
    extra_info: list[dict] | None = None,
) -> str:
    """
    Build a pallet label from a stored template and fill summary fields + optional products list.
    Adjust ^FN numbers to match your actual printer template.
    """
    try:
        zpl_lines = [
            "^XA",
            f"^XFE:{label_type}.ZPL^FS",
        ]

        if label_summary_info:
            zpl_lines.extend(
                [
                    f"^FN1^FD{label_summary_info.get('pallet_id', '')}^FS",
                    f"^FN2^FD{int(label_summary_info.get('pallet_quantity', 0))}^FS",
                    f"^FN3^FD{label_summary_info.get('gross_weight', '')}^FS",
                    f"^FN4^FD{label_summary_info.get('pallet_dimensions', '')}^FS",
                    f"^FN5^FD{label_summary_info.get('combo_pallet_ids', '')}^FS",
                    f"^FN6^FD{label_summary_info.get('gross_weight', '')}^FS",
                    f"^FN7^FD{label_summary_info.get('gross_dimensions', '')}^FS",
                ]
            )

        if extra_info is not None:
            zpl_lines.append(add_products_to_label(extra_info))

        zpl_lines.append("^XZ")
        return "\n".join(zpl_lines)
    except Exception as ex:
        print("Data could not be processed: \n", ex)
        return ""


def create_combined_pallet_label_data(combined_summary: dict, combined_ids: str) -> str:
    """
    Simple combined pallet label that also prints the combined IDs.
    Uses the same ^FN mappings as create_pallet_label_zpl and adds ^FN8 for IDs.
    """
    label_type = "PALCOMBO"
    zpl_lines = f"""^XA
        ^XFE:{label_type}.ZPL^FS
        ^FN3^FD{str(combined_ids)}^FS
        ^FN1^FD{int(combined_summary.get('gross_weight', 0))}^FS
        ^FN2^FD{int(combined_summary.get('gross_height', 0))}^FS
        ^XZ"""

    return zpl_lines


def add_products_to_label(pallet_products: list[dict]) -> str:
    """
    Render the (up to) first 7 product lines onto the label body.
    Adjust coordinates/text sizes to match your actual template.
    """
    try:
        zpl = ""

        # "More than 6" => mixed pallet
        if len(pallet_products) > 6:
            zpl += "^FO350,420^A0,22^FDMIXED PALLET^FS"
        else:
            y_positions = [410, 380, 350, 320, 290, 260, 230]
            for idx, product in enumerate(pallet_products[:7]):
                y = y_positions[idx]
                total = int(product.get("total", 0))
                desc = product.get("product_description", "")
                zpl += (
                    f"\n^FO{y},420^A0,22^FD{total}^FS" f"\n^FO{y},480^A0,22^FD{desc}^FS"
                )

        return zpl
    except Exception as ex:
        print("Data could not be processed: \n", ex)
        return ""
