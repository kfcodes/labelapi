from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_GTIN14_RE = re.compile(r"^\d{14}$")
_GTIN13_RE = re.compile(r"^\d{13}$")
_GTIN8_RE = re.compile(r"^\d{8}$")
_SSCC_RE = re.compile(r"^\d{18}$")
_DATE_YYMMDD_RE = re.compile(r"^\d{6}$")
_DATE_YYYY_MM_DD_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _mod10_check_digit(num_without_cd: str) -> int:
    total, weight = 0, 3
    for ch in reversed(num_without_cd):
        total += int(ch) * weight
        weight = 1 if weight == 3 else 3
    return (10 - (total % 10)) % 10


def valid_gtin(s: str) -> bool:
    if not s or not s.isdigit() or len(s) not in (8, 12, 13, 14):
        return False
    body, cd = s[:-1], int(s[-1])
    return _mod10_check_digit(body) == cd


def pad_gtin_to_14(s: str) -> Optional[str]:
    if not s or not s.isdigit() or len(s) > 14:
        return None
    s14 = s.zfill(14)
    body = s14[:-1]
    return body + str(_mod10_check_digit(body))


def normalize_gtin14(
    raw: Optional[str], value_options: Mapping[str, Any] | None
) -> Optional[str]:
    if not raw:
        return None
    raw = str(raw)
    if len(raw) == 14 and valid_gtin(raw):
        return raw
    pad = (
        bool(value_options.get("pad_gtin_to_14", False))
        if isinstance(value_options, dict)
        else False
    )
    if pad:
        padded = pad_gtin_to_14(raw)
        if padded and valid_gtin(padded):
            return padded
    return raw if valid_gtin(raw) else None


def normalize_expiry(src: Optional[str], target_fmt: str = "YYMMDD") -> Optional[str]:
    if not src:
        return None
    s = str(src)
    try:
        if _DATE_YYMMDD_RE.match(s):
            dt = datetime.strptime(s, "%y%m%d")
        elif _DATE_YYYY_MM_DD_RE.match(s):
            dt = datetime.strptime(s, "%Y-%m-%d")
        else:
            return None
        if target_fmt == "YYMMDD":
            return dt.strftime("%y%m%d")
        if target_fmt == "YYYYMMDD":
            return dt.strftime("%Y%m%d")
        if target_fmt == "YYYY-MM-DD":
            return dt.strftime("%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def _json_load_maybe(v: Any) -> Any:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return v
    return v


def verify_barcode_formats_against_record(
    record: Mapping[str, Any],
    barcode_formats: Sequence[Mapping[str, Any]],
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    for fmt in barcode_formats:
        sym = (fmt.get("symbology") or "").upper()
        name = fmt.get("format_name") or "unknown_format"
        ai_order = _json_load_maybe(fmt.get("gs1_ai_order")) or []
        value_opts = _json_load_maybe(fmt.get("value_options")) or {}

        if sym == "GS1_128":
            # GTIN-14
            if "gtin14" in ai_order:
                gtin = normalize_gtin14(
                    record.get("gtin14")
                    or record.get("gtin")
                    or record.get("case_gtin")
                    or record.get("unit_gtin"),
                    value_opts,
                )
                if not gtin:
                    errors.append(f"[{name}] GTIN-14 missing/invalid.")
                elif len(gtin) != 14:
                    warnings.append(
                        f"[{name}] GTIN present but not 14 digits after normalization."
                    )

            # CONTENT GTIN-14
            if "content_gtin14" in ai_order:
                cgtin = normalize_gtin14(
                    record.get("content_gtin14")
                    or record.get("case_gtin")
                    or record.get("gtin14"),
                    value_opts,
                )
                if not cgtin:
                    errors.append(f"[{name}] CONTENT GTIN-14 missing/invalid.")

            # SSCC
            if "sscc" in ai_order:
                s = record.get("sscc")
                if not (isinstance(s, str) and _SSCC_RE.match(s)):
                    errors.append(f"[{name}] SSCC must be 18 digits.")
                elif not valid_gtin(s):
                    errors.append(f"[{name}] SSCC check digit invalid.")

            # LOT/BATCH
            if "lot" in ai_order and not (
                record.get("lot") or record.get("batch_code")
            ):
                errors.append(f"[{name}] LOT/BATCH required but not found.")

            # SERIAL
            if "serial" in ai_order and not record.get("serial"):
                errors.append(f"[{name}] SERIAL required but not found.")

            # EXP
            if "exp" in ai_order:
                src = (
                    record.get("exp")
                    or record.get("expiry_date")
                    or record.get("bbe_date")
                )
                want = (
                    value_opts.get("exp_format")
                    if isinstance(value_opts, dict)
                    else None
                ) or "YYMMDD"
                norm = normalize_expiry(src, want) if src else None
                if not norm:
                    errors.append(f"[{name}] EXP required but missing/invalid date.")
                elif want == "YYMMDD" and not re.compile(r"^\d{6}$").match(norm):
                    errors.append(f"[{name}] EXP not YYMMDD after normalization.")

        elif sym in ("EAN_13", "EAN_8", "ITF_14", "CODE_128"):
            if sym == "EAN_13":
                val = record.get("gtin") or record.get("unit_gtin")
                if not (
                    isinstance(val, str) and _GTIN13_RE.match(val) and valid_gtin(val)
                ):
                    errors.append(f"[{name}] Requires valid 13-digit GTIN.")
            elif sym == "EAN_8":
                val = record.get("gtin8")
                if not (
                    isinstance(val, str) and _GTIN8_RE.match(val) and valid_gtin(val)
                ):
                    errors.append(f"[{name}] Requires valid 8-digit GTIN.")
            elif sym == "ITF_14":
                val = record.get("gtin14") or record.get("case_gtin")
                if not (
                    isinstance(val, str) and _GTIN14_RE.match(val) and valid_gtin(val)
                ):
                    errors.append(f"[{name}] Requires valid 14-digit GTIN.")
            elif sym == "CODE_128":
                if not (record.get("code128_raw") or record.get("barcode_data")):
                    errors.append(f"[{name}] Requires 'code128_raw' or 'barcode_data'.")
        elif sym == "HR_TEXT":
            opts = _json_load_maybe(fmt.get("value_options")) or {}
            template = (opts or {}).get("template", "")
            needed = re.findall(r"{([a-zA-Z0-9_]+)}", template)
            for n in needed:
                if n.startswith("exp_"):
                    if not (
                        record.get("exp")
                        or record.get("expiry_date")
                        or record.get("bbe_date")
                    ):
                        warnings.append(f"[{name}] Template needs expiry; none found.")
                elif not record.get(n):
                    warnings.append(
                        f"[{name}] Template placeholder '{n}' not found; will render empty."
                    )
        else:
            warnings.append(f"[{name}] Unknown symbology '{sym}' — skipped validation.")

    return errors, warnings
