# app/database/write_db.py
from app.database.db_connection import db


def update_pallet_packing_list(palletid: int, site: str) -> None:
    """
    Calls stored procedure UpdateOrInsertPackingList(palletid, site).
    """
    try:
        connection = db().raw_connection()
        cursor = connection.cursor()
        cursor.execute(f"Call UpdateOrInsertPackingList({int(palletid)},'{str(site)}')")
        cursor.close()
        connection.commit()
        print(
            f"Called UpdateOrInsertPackingList on pallet: {int(palletid)}, location: {str(site)}"
        )
    except Exception as ex:
        print("DB write failed:\n", ex)
        raise
