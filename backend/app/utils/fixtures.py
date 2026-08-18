import pickle
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")

FIXTURE_DIR = Path(__file__).parents[2] / "dev_fixtures"


def save_pickle(coral_name: str, name: str, value: object) -> None:
    path = FIXTURE_DIR / coral_name / f"{name}.pkl"
    with path.open("wb") as f:
        pickle.dump(value, f)


def load_pickle(coral_name: str, name: str) -> T:
    path = FIXTURE_DIR / coral_name / f"{name}.pkl"
    with path.open("rb") as f:
        return pickle.load(f)