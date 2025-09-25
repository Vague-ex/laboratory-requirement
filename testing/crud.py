from pymongo.collection import Collection
from .models import Item

def get_all_items(collection: Collection):
    return list(collection.find({}, {"_id": 0}))

def insert_item(collection: Collection, item: Item):
    collection.insert_one(item.dict())
    return {"status": "inserted"}

def update_item(collection: Collection, name: str, data: dict):
    collection.update_one({"name": name}, {"$set": data})
    return {"status": "updated"}

def delete_item(collection: Collection, name: str):
    collection.delete_one({"name": name})
    return {"status": "deleted"}
