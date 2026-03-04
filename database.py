import os
import json
from typing import Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")


def load_data() -> Dict:
    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r") as f:
        content = f.read().strip()
        if not content:
            return {}

        return json.loads(content)


def save_data(data: Dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)