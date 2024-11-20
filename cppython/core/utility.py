"""Core Utilities"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def read_json(path: Path) -> Any:
    """Reading routine

    Args:
        path: The json file to read

    Returns:
        The json data
    """
    with open(path, encoding='utf-8') as file:
        return json.load(file)


def write_model_json(path: Path, model: BaseModel) -> None:
    """Writing routine. Only writes model data

    Args:
        path: The json file to write
        model: The model to write into a json
    """
    serialized = json.loads(model.model_dump_json(exclude_none=True))
    with open(path, 'w', encoding='utf8') as file:
        json.dump(serialized, file, ensure_ascii=False, indent=4)


def write_json(path: Path, data: Any) -> None:
    """Writing routine

    Args:
        path: The json to write
        data: The data to write into json
    """
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
