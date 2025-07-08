import json
import os

MAP_FILE = "mappings.json"

def load_map():
    if not os.path.exists(MAP_FILE):
        return {}
    with open(MAP_FILE, "r") as f:
        return json.load(f)

def save_map(mapping):
    with open(MAP_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

def add_mapping(source_id, target_id):
    mapping = load_map()
    mapping[str(source_id)] = target_id
    save_map(mapping)
