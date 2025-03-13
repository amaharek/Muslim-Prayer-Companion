"""
Constants for the Muslim Prayer Companion component.
"""

from typing import Final
from logging import getLogger

DOMAIN: Final = "muslim_prayer_companion"
NAME: Final = "Muslim Prayer Companion"
PRAYER_TIMES_ICON: Final = "mdi:calendar-clock"

CONF_CALC_METHOD: Final = "calculation_method"
CONF_USE_API: Final = "use_api"  # Option to choose API-based prayer times.
CONF_API_KEY: Final = "api_key"  # API key if required.
CONF_IQAMAH_OFFSETS: Final = "iqamah_offsets"  # Offsets (in minutes) for Iqamah times.

DEFAULT_IQAMAH_OFFSETS = {
    "Fajr": 20,
    "Dhuhr": 15,
    "Asr": 15,
    "Maghrib": 10,
    "Isha": 15
}

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
    "ie-hicc"
]

DEFAULT_CALC_METHOD: Final = "ie-icci"
DATA_UPDATED: Final = "muslim_prayer_data_updated"

LOGGER = getLogger(__package__)