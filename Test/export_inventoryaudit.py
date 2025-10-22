import os
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import json_util

# Reuse the MongoDB connection string from a.py
try:
    from a import MONGO_URI
except Exception as import_error:
    raise RuntimeError("Unable to import MONGO_URI from a.py. Ensure a.py defines MONGO_URI.") from import_error


DB_NAME = "inventoryaudit"


def get_db(mongo_uri: str, db_name: str):
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=20000)
    # Validate connection
    client.admin.command("ping")
    return client[db_name]


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def export_collections_to_json(db_name: str = DB_NAME, output_dir: str | None = None, pretty: bool = True) -> list[str]:
    """
    Export all collections from the specified database to JSON files.

    Returns a list of written file paths.
    """
    try:
        db = get_db(MONGO_URI, db_name)
    except ServerSelectionTimeoutError as conn_err:
        raise RuntimeError(f"Could not connect to MongoDB: {conn_err}") from conn_err

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_output_dir = output_dir or os.path.join("exports", f"{db_name}-{timestamp}")
    ensure_dir(base_output_dir)

    collections = db.list_collection_names()
    if not collections:
        return []

    written_files: list[str] = []
    for collection_name in collections:
        documents = list(db[collection_name].find({}))
        file_path = os.path.join(base_output_dir, f"{db_name}_{collection_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(documents, f, default=json_util.default, ensure_ascii=False, indent=2)
            else:
                json.dump(documents, f, default=json_util.default, ensure_ascii=False)
        written_files.append(file_path)

    return written_files


if __name__ == "__main__":
    files = export_collections_to_json()
    if files:
        print("Export complete. Files written:")
        for p in files:
            print(f"- {p}")
    else:
        print(f"No collections found in database '{DB_NAME}'.")


