from db_access_layer.db_connection import db

def update_pallet_packing_list(id):
    try:
        print(f"palleid passed to function: {id}")
        connection = db().raw_connection()
        cursor = connection.cursor()
        cursor.execute(f'Call UpdateOrInsertPackingList({id})');
        cursor.close()
        connection.commit()
        print("Called the stored function")
    except Exception as ex:
        print("Connection could not be made due to the following error: \n", ex)
