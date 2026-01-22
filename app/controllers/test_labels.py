from __future__ import annotations

from typing import Dict, List

from app.printer_connection.zpl_printer_logic import label_printer_connection

# from app.zpl.test_label_zpl_logic import (
#     build_gs1_datamatrix_fd,
#     build_template_zpl,
#     create_test_label_zpl,
# )


async def test_label_function() -> str:
    try:
        # 1) Build the template block first (stores template on printer)
        # template_block = build_template_zpl()

        # 2) Build jobs for each label dict using your existing generator
        # jobs: List[str] = []
        # for item in labels:
        #     job = create_test_label_zpl(item)  # expects ONE dict
        #     jobs.append(job)

        # 3) Combine template + all jobs and send
        # payload = template_block + "\n" + "\n".join(jobs)
        # return label_printer_connection(payload, "192.168.1.132", 9100)

        # return label_printer_connection(zpl_payload, "192.168.1.132", 9100)
        return label_printer_connection("test", "192.168.1.132", 9100)
        # print(payload)
        # return payload

    except Exception as ex:
        print("Label could not be created due to: \n", ex)
        return ""
