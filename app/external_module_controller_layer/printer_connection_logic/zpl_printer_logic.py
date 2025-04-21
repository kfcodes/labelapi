import socket


def label_printer_connection(zpl_string: str, printer_address: str, printer_port: int) -> dict:
    try:
        label = zpl_string.encode(encoding="ascii", errors="ignore")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mysocket:
            mysocket.connect((printer_address, printer_port))
            mysocket.send(label)
        return {
            "status": "success",
            "printer": f"{printer_address}:{printer_port}",
            "message": zpl_string
        }
    except Exception as ex:
        return {
            "status": "error",
            "printer": f"{printer_address}:{printer_port}",
            "error": str(ex)
        }
