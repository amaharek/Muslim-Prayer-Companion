"""
Constants for the Islamic Prayer component.
"""

from typing import Final
from logging import Logger, getLogger

DOMAIN: Final = "muslim-prayer-companion"
NAME: Final = "Muslim Prayer Companion"
PRAYER_TIMES_ICON = "mdi:calendar-clock"

CONF_CALC_METHOD: Final = "calculation_method"

CALC_METHODS = [
    "jafari",
    "karachi",
    "isna",
    "mwl",
    "makkah",
    "egypt",
    "tehran",
    "gulf",
    "kuwait",
    "qatar",
    "singapore",
    "france",
    "turkey",
    "russia",
    "ie-icci",
    "ie-mcnd",
    "ie-hicc",
]

DEFAULT_CALC_METHOD: Final = "ie-icci"

DATA_UPDATED = "Islamic_prayer_data_updated"
LOGGER: Logger = getLogger(__package__)
