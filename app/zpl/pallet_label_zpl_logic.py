from typing import Any, Mapping, Sequence

from app.static_json_readers.pallet_json_readers import (
    get_pallet_variables,
    load_pallet_config,
)


def create_pallet_label_zpl(
    label_type: str,  # the structure name to call (^XFE:{label_type}.ZPL^FS)
    label_summary_info: (
        Mapping[str, Any] | None
    ) = None,  # dict with keys from PALLETVARIABLES
    extra_info: list[dict] | None = None,  # optional products
    *,
    copies: int = 1,  # how many labels to print
) -> str:
    """
    Build a pallet label ZPL using the stored template and PALLETVARIABLES mapping.

    - Calls ^XFE:{label_type}.ZPL^FS
    - Emits ^FN{n}^FD{value}^FS ONLY for keys present in PALLETVARIABLES
      and provided in label_summary_info
    - Renders optional product rows
    - Ensures ^XA/^XZ and UTF-8 (^CI28)
    - Prints the requested number of copies via ^PQ
    """
    load_pallet_config()
    vars_map = get_pallet_variables()  # name -> fn:int

    def _fd_escape(val: Any) -> str:
        return str(val).replace("^", " ").replace("~", " ")

    def _ensure_xa_xz(zpl: str) -> str:
        s = zpl.strip()
        u = s.upper()
        if not u.startswith("^XA"):
            s = "^XA\n" + s
        if not s.upper().endswith("^XZ"):
            s = s + "\n^XZ"
        return s

    def _ensure_utf8(zpl: str) -> str:
        if "^CI28" in zpl.upper():
            return zpl
        head, _, tail = zpl.partition("\n")
        if head.upper().startswith("^XA"):
            return f"{head}\n^FX UTF-8 ^CI28\n{tail}"
        return "^CI28\n" + zpl

    info = dict(label_summary_info or {})

    lines: list[str] = [
        "^XA",
        "^CI28",
        f"^XFE:{label_type}.ZPL^FS",  # call stored format by name
        f"^PQ{max(int(copies), 1)}",  # copies, minimum 1
    ]

    # Inject values in a deterministic order (sorted by FN number)
    for key, fn in sorted(vars_map.items(), key=lambda kv: kv[1]):
        if key in info:
            lines.append(f"^FN{fn}^FD{_fd_escape(info[key])}^FS")

    if extra_info is not None:
        lines.append(_add_products_block(extra_info))

    lines.append("^XZ")

    zpl = "\n".join(lines)
    return _ensure_utf8(_ensure_xa_xz(zpl))


def _add_products_block(pallet_products: Sequence[Mapping[str, Any]]) -> str:
    out: list[str] = []

    # tweak to your layout (^FOx,y with x first)
    x_qty = 350
    x_desc = 480
    y_positions = [230, 260, 290, 320, 350, 380, 410]
    font_cmd = "^A0,22"

    products = list(pallet_products)

    if len(products) > 6:
        out.append("^FO350,420^A0,22^FDMIXED PALLET^FS")
        return "\n".join(out)

    for idx, product in enumerate(products[:7]):
        y = y_positions[idx]
        try:
            total_i = int(product.get("total", 0))
        except (TypeError, ValueError):
            total_i = 0
        desc = (
            str(product.get("product_description", ""))
            .replace("^", " ")
            .replace("~", " ")
        )
        out.append(f"^FO{x_qty},{y}{font_cmd}^FD{total_i}^FS")
        out.append(f"^FO{x_desc},{y}{font_cmd}^FD{desc}^FS")

    return "\n".join(out)
