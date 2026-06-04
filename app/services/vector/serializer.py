import json
from pathlib import Path


def save_metadata(
    path: Path,
    docs: list[dict],
):

    with open(path, "w", encoding="utf-8") as f:

        json.dump(
            docs,
            f,
            ensure_ascii=False,
            indent=2,
        )


def load_metadata(
    path: Path,
) -> list[dict]:

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)