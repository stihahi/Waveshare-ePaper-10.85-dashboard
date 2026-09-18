import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float


def load_location(path, default):
    try:
        with open(path) as location_file:
            coordinates = json.load(location_file)
    except FileNotFoundError:
        return default
    return Location(latitude=float(coordinates['latitude']), longitude=float(coordinates['longitude']))
