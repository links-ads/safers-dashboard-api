from dataclasses import dataclass


@dataclass
class AoiData:
    latitude: float
    longitude: float


# just some helper constants to set default locations
NAMED_AOIS = {
    "athens": AoiData(37.983810, 23.727539),
    "edinburgh": AoiData(55.953251, -3.188267),
    "paris": AoiData(48.864716, 2.349014),
    "rome": AoiData(41.902782, 12.496366),
}
