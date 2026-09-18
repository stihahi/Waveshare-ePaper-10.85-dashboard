import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class LocalConfig:
    location: Location
    dgx_spark_hosts: dict  # display label -> SSH host


def load_local_config(path, default):
    try:
        with open(path) as config_file:
            sections = json.load(config_file)
    except FileNotFoundError:
        return default
    return LocalConfig(location=_parse_location(sections, default.location),
                       dgx_spark_hosts=sections.get('dgx_spark_hosts', default.dgx_spark_hosts))


def _parse_location(sections, default):
    if 'location' not in sections:
        return default
    coordinates = sections['location']
    return Location(latitude=float(coordinates['latitude']), longitude=float(coordinates['longitude']))
