from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Optional, Tuple, Union

from app.printer_connection.zpl_printer_logic import label_printer_connection
from app.static_json_readers.box_json_readers import get_all_box_label_zpl
from app.static_json_readers.pallet_json_readers import get_all_pallet_label_zpl

Printer = Dict[str, Union[str, int]]
Logger = Callable[[str], None]


def _upload_bundle_to_printers(
    zpl_bundle: str,
    printers: Iterable[Printer],
    *,
    dry_run: bool = True,
    logger: Optional[Logger] = print,
) -> str:
    """
    Common helper to send a ZPL bundle to multiple printers.
    Returns the bundle when dry_run=True, else joined printer responses.
    """
    log = logger or (lambda *_: None)

    if dry_run:
        log("--- DRY RUN: ZPL BUNDLE ---")
        log(zpl_bundle)
        log("--- END DRY RUN ---")
        return zpl_bundle

    responses: List[str] = []
    for p in printers:
        ip = str(p["ip"])
        port = int(p["port"])
        try:
            resp = label_printer_connection(zpl_bundle, ip, port)
            log(f"synced to printer {ip}:{port}")
            responses.append(str(resp))
        except Exception as e:
            msg = f"ERROR syncing to {ip}:{port} -> {e}"
            log(msg)
            responses.append(msg)

    return "\n".join(responses)


def upload_pallet_label_structures_to_printers(
    printers: List[Printer],
    *,
    dry_run: bool = True,
    logger: Optional[Logger] = print,
) -> str:
    """
    Compile ALL pallet label structures into one ZPL bundle and upload to each printer.
    """
    try:
        zpl = get_all_pallet_label_zpl(validate=True)
        return _upload_bundle_to_printers(zpl, printers, dry_run=dry_run, logger=logger)
    except Exception as ex:
        (logger or print)(
            f"Pallet label structures could not be uploaded due to:\n {ex}"
        )
        return f"Error: {ex}"


def upload_internal_label_structures_to_printers(
    printers: List[Printer],
    *,
    dry_run: bool = True,
    logger: Optional[Logger] = print,
) -> str:
    """
    If 'internal' uses the same pallet bundle, this just forwards to the same logic.
    Change to a different generator if internal labels differ.
    """
    try:
        zpl = get_all_pallet_label_zpl(validate=True)
        return _upload_bundle_to_printers(zpl, printers, dry_run=dry_run, logger=logger)
    except Exception as ex:
        (logger or print)(
            f"Internal pallet label structures could not be uploaded due to:\n {ex}"
        )
        return f"Error: {ex}"


def upload_box_label_structures_to_printers(
    printers: List[Printer],
    *,
    dry_run: bool = True,
    logger: Optional[Logger] = print,
) -> str:
    """
    Compile ALL box label structures into one ZPL bundle and upload to each printer.
    """
    try:
        zpl = get_all_box_label_zpl(validate=True)
        return _upload_bundle_to_printers(zpl, printers, dry_run=dry_run, logger=logger)
    except Exception as ex:
        (logger or print)(f"Box label structures could not be uploaded due to:\n {ex}")
        return f"Error: {ex}"
