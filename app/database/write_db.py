from sqlalchemy import text

from app.database.db_connection import db


def write_db(selection: str):
    """
    Executes a write statement (INSERT/UPDATE/DELETE) and returns a dict
    with the affected row count.
    """
    print("SELECTION")
    print(selection)
    try:
        engine = db()  # same db() your read_db uses
        with engine.begin() as conn:  # handles commit/rollback
            result = conn.execute(text(selection))
            return {"rowcount": result.rowcount}
    except Exception as ex:
        print("DB write failed:\n", ex)
        raise


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
