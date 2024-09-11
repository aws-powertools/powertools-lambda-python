from __future__ import annotations

from enum import Enum


class MetricUnit(Enum):
    Seconds = "Seconds"
    Microseconds = "Microseconds"
    Milliseconds = "Milliseconds"
    Bytes = "Bytes"
    Kilobytes = "Kilobytes"
    Megabytes = "Megabytes"
    Gigabytes = "Gigabytes"
    Terabytes = "Terabytes"
    Bits = "Bits"
    Kilobits = "Kilobits"
    Megabits = "Megabits"
    Gigabits = "Gigabits"
    Terabits = "Terabits"
    Percent = "Percent"
    Count = "Count"
    BytesPerSecond = "Bytes/Second"
    KilobytesPerSecond = "Kilobytes/Second"
    MegabytesPerSecond = "Megabytes/Second"
    GigabytesPerSecond = "Gigabytes/Second"
    TerabytesPerSecond = "Terabytes/Second"
    BitsPerSecond = "Bits/Second"
    KilobitsPerSecond = "Kilobits/Second"
    MegabitsPerSecond = "Megabits/Second"
    GigabitsPerSecond = "Gigabits/Second"
    TerabitsPerSecond = "Terabits/Second"
    CountPerSecond = "Count/Second"
    NoUnit = "None"


class MetricResolution(Enum):
    Standard = 60
    High = 1
