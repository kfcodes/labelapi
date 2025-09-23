import pandas as pd

from app.database.db_connection import db


def read_db(selection: str):
    """
    Returns a dict indexed by row number -> row dict
    (matches existing callers that do .values()).
    """
    print("SELECTION")
    print(selection)
    try:
        info = pd.read_sql(selection, db())
        return info.to_dict(orient="index")
    except Exception as ex:
        print("DB read failed:\n", ex)
        raise


def read_to_list_index(selection: str):
    """
    Returns a list[dict] (records). Existing code does result[0] afterward.
    """
    try:
        info = pd.read_sql(selection, db())
        return info.to_dict(orient="records")
    except Exception as ex:
        print("DB read (records) failed:\n", ex)
        raise
