from db_access_layer.db_connection import db

def update_pallet_packing_list(palletid, site):
    try:
        print(f"palleid passed to function: {palletid}")
        connection = db().raw_connection()
        cursor = connection.cursor()
        cursor.execute(f'Call UpdateOrInsertPackingList({palletid},{site})')
        cursor.close()
        connection.commit()
        print("Called the stored function to create or set packing list")
    except Exception as ex:
        print("Connection could not be made due to the following error: \n", ex)
