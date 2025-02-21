"""Enums for validation"""

from enum import Enum


class PlaceTypeNews(str, Enum):
    PLANNING_REGIONS = "PR"
    COUNTY = "CTY"
    ADMINISTRATIVE_UNIT = "AU"
    LOCAL_ADMINISTRATIVE_UNITS = "LAU"


class RangeOrRecency(str, Enum):
    RANGE = "RANGE"
    RECENCY = "RECENCY"


class NewsTopic(str, Enum):
    BATTERY_STORAGE = "batteryStorage"
    GRID_EXPANSION = "gridExpansion"
    SOLAR = "solar"
    HYDROGEN = "hydrogen"
    WIND = "wind"
