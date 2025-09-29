from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple, Union

from dotenv import load_dotenv
from fastapi import Request

from app.database.read_db import read_db
from app.printer_connection.zpl_printer_logic import label_printer_connection
from app.static_json_readers import get_compiled_box_label_zpl
from app.static_json_readers import (
    validate_placeholder_usage as validate_box_placeholder_usage,
)
from app.static_json_readers.box_json_readers import get_all_box_label_zpl
from app.zpl.box_label_zpl_logic import create_box_label_zpl

from .printers import PrinterConn, get_printers_for_site, resolve_site_id_from_request

BASE_DIR = Path(__file__).resolve().parents[1]  # -> app/
load_dotenv(BASE_DIR / "env" / "box_label.env")


# --------------------------
# Internal helpers
# --------------------------
def _choose_role_from_label_size(
    label_size: Union[str, int], explicit_role: Optional[str]
) -> str:
    """
    If role is explicitly provided, use it.
    Otherwise choose based on label_size: 1 -> 'large', else 'small'.
    """
    if explicit_role in {"large", "small"}:
        return explicit_role
    try:
        return "large" if int(label_size) == 1 else "small"
    except Exception:
        return "large"


def _select_printer(
    site_id: str,
    *,
    label_size: Union[str, int],
    preferred_line: Optional[str] = None,
    preferred_role: Optional[str] = None,
) -> Tuple[PrinterConn, str, str]:
    """
    Pick a printer connection for the site. If preferred_line/role are provided, try those first.
    Otherwise, derive role (large/small) from label_size and pick the first line that matches.
    Returns: (conn, selected_line, selected_role)
    """
    per_line = get_printers_for_site(site_id)
    role = _choose_role_from_label_size(label_size, preferred_role)

    # explicit line preference
    if preferred_line and preferred_line in per_line:
        line_roles = per_line[preferred_line]
        if role in line_roles:
            return line_roles[role], preferred_line, role
        # if requested role unavailable, fall back to any available role on that line
        for r, conn in line_roles.items():
            return conn, preferred_line, r

    # fallback: first line that has the requested role
    for ln, roles in per_line.items():
        if role in roles:
            return roles[role], ln, role

    # final fallback: any available printer on any line
    for ln, roles in per_line.items():
        for r, conn in roles.items():
            return conn, ln, r

    raise ValueError(f"No printers defined for site '{site_id}'")


# --------------------------
# Public API used by routes
# --------------------------
async def main_print_box_label_function(
    request: Request,
    unique_id: Union[str, int],
    quantity: int,
    *,
    line: Optional[str] = None,  # e.g. "line1" – optional hint
    role: Optional[str] = None,  # "large" | "small" – optional override
    dry_run: bool = False,
    timeout: float = 3.0,
) -> str:
    """
    Build the BOX label ZPL from DB, resolve the caller's site from their IP,
    auto-select the correct printer (large/small), and send (or print) the job.

    Returns:
        str: printer response (or the ZPL itself if dry_run=True)
    """
    # 1) Pull record from DB and let your existing logic render the final ZPL
    #    (create_box_label_zpl should embed the correct structure and fields)
    recs = read_db(f"{os.getenv('PRODUCTIONLABELINFO')}{unique_id}")
    if not recs:
        raise ValueError(f"No label record found for id '{unique_id}'")
    box_label_info: Mapping[str, Union[str, int]] = recs[0]
    zpl_string = create_box_label_zpl(box_label_info, quantity)

    # 2) Resolve site-id from the request IP and pick a printer
    site_id = await resolve_site_id_from_request(request)
    conn, selected_line, selected_role = _select_printer(
        site_id,
        label_size=box_label_info.get("label_size", 1),
        preferred_line=line,
        preferred_role=role,
    )

    # 3) Print or dry-run
    if dry_run:
        print(
            f"--- DRY RUN BOX LABEL -> {conn['ip']}:{conn['port']} "
            f"(site {site_id}, {selected_line}/{selected_role}) ---"
        )
        print(zpl_string)
        print("--- END ZPL ---")
        return zpl_string

    response = label_printer_connection(
        zpl_string, conn["ip"], conn["port"], timeout=timeout
    )
    return response


async def upload_box_label_structures_to_printers(
    printers: List[Dict[str, Union[str, int]]],
    *,
    dry_run: bool = True,
) -> str:
    """
    Compile ALL box label structures into one ZPL bundle and upload to each printer.

    Args:
        printers: list like [{"ip": "192.168.1.42", "port": 9100}, ...]
        dry_run:  if True, print the ZPL bundle and return it without sending

    Returns:
        The compiled ZPL bundle (if dry_run), otherwise newline-joined printer responses.
    """
    try:
        # Build one ZPL stream containing ALL BOX structures, with validations/enforcers
        zpl = get_all_box_label_zpl(validate=True)

        if dry_run:
            print("--- DRY RUN: BOX STRUCTURES ZPL BUNDLE ---")
            print(zpl)
            print("--- END DRY RUN ---")
            return zpl

        responses: List[str] = []
        for p in printers:
            ip = str(p["ip"])
            port = int(p["port"])
            try:
                resp = label_printer_connection(zpl, ip, port)
                print(f"synced to printer {ip}:{port}")
                responses.append(str(resp))
            except Exception as e:
                msg = f"ERROR syncing to {ip}:{port} -> {e}"
                print(msg)
                responses.append(msg)

        return "\n".join(responses)

    except Exception as ex:
        print("Box label structures could not be uploaded due to:\n", ex)
        return f"Error: {ex}"
