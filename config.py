from typing import TypedDict
from json import load

class _MoodleConfig(TypedDict):
    AppURL: str

class _AccountConfig(TypedDict):
    Username: str
    Password: str

class Config(TypedDict):
    Moodle: _MoodleConfig
    Account: _AccountConfig


def load_config() -> Config:
    with open("Pache.json") as f:
        return load(f)