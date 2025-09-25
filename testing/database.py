from pymongo import MongoClient

def get_database(connection_str: str, db_name: str):
    client = MongoClient(connection_str)
    return client[db_name]
