import pandas as pd
import os
from db_access_layer.db_connection import db

def read_to_list_index(selection):
    try:
        info = pd.read_sql(selection ,db())
        values = info.to_dict(orient='index')
        return values
    except Exception as ex:
        print("Connection could not be made due to the following error: \n", ex)
