import os
import json
from glob import glob
from typing import Iterable, List, Dict, Any


CORE_PRESET = [
    "_id",
    "itemId",
    "ItemID",
    "quantity",
    "unitPrice",
    "extendedValue",
    "auditDate",
]

META_PRESET = [
    "_id",
    "description",
    "desc",
    "category",
    "supplier",
]


def filter_document(document: Dict[str, Any], keys: Iterable[str]) -> Dict[str, Any]:
    return {k: document[k] for k in keys if k in document}


def read_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def write_json(path: str, data: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def filter_folder(input_path: str, output_path: str, keep_keys: Iterable[str]):
    # Collect files
    files: List[str] = []
    if os.path.isdir(input_path):
        files = glob(os.path.join(input_path, "**", "*.json"), recursive=True)
    elif os.path.isfile(input_path) and input_path.lower().endswith(".json"):
        files = [input_path]
    else:
        raise ValueError("input_path must be a JSON file or a directory containing JSON files")

    all_docs: List[Dict[str, Any]] = []
    for fp in files:
        try:
            all_docs.extend(read_json(fp))
        except Exception:
            # skip unreadable files
            pass

    filtered = [filter_document(doc, keep_keys) for doc in all_docs]
    write_json(output_path, filtered)
    return {"read_files": len(files), "written": len(filtered), "output": output_path}


if __name__ == "__main__":
    # Example usage presets:
    # 1) Core fields only -> outputs to filtered_core.json
    # 2) Meta fields only -> outputs to filtered_meta.json
    import argparse

    parser = argparse.ArgumentParser(description="Filter JSON documents to selected keys and write to a new JSON file.")
    parser.add_argument("input", help="Input JSON file or directory")
    parser.add_argument("output", help="Output JSON file path")
    parser.add_argument("--preset", choices=["core", "meta"], help="Use a preset set of keys")
    parser.add_argument("--keys", nargs="*", help="Custom keys to keep (overrides preset if provided)")

    args = parser.parse_args()

    if args.keys:
        keep = args.keys
    elif args.preset == "core":
        keep = CORE_PRESET
    elif args.preset == "meta":
        keep = META_PRESET
    else:
        raise SystemExit("Provide --preset core|meta or --keys <k1> <k2> ...")

    result = filter_folder(args.input, args.output, keep)
    print(result)


