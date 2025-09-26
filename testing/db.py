from pymongo import MongoClient

class MongoDBConnection:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        return self.db

    def get_collections(self):
        if self.db:
            return self.db.list_collection_names()
        return []
