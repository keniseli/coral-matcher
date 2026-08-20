import pickle
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")

FIXTURES_DIRECTORY = Path(__file__).parents[2] / "dev_fixtures"


def save_pickle(coral_name: str, name: str, value: object) -> None:
    path = FIXTURES_DIRECTORY / coral_name / f"{name}.pkl"
    with path.open("wb") as f:
        pickle.dump(value, f)


def load_pickle(coral_name: str, name: str) -> T:
    path = FIXTURES_DIRECTORY / coral_name / f"{name}.pkl"
    with path.open("rb") as f:
        return pickle.load(f)

def get_fixture_image_path(coral_name: str, image_name: str | None = None) -> Path:
    base_dir = Path(__file__).parents[2]
    if image_name is None:
        path = sorted((base_dir / FIXTURES_DIRECTORY / coral_name).glob("*.jpg"))[0]
    else:
        path = base_dir / FIXTURES_DIRECTORY / coral_name / image_name
    
    return path