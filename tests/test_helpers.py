"""
Test helpers for Muslim Prayer Companion integration.
This module provides utility functions and fixtures to create fake Home Assistant
objects, dummy config entries, and sample prayer/hijri data for testing.
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock


def create_fake_hass():
    """Return a fake HomeAssistant instance with minimal configuration."""
    hass = MagicMock()
    # Provide fake latitude and longitude
    hass.config.latitude = 51.5074  # e.g. London latitude
    hass.config.longitude = -0.1278  # e.g. London longitude

    # Simulate async_add_executor_job by simply calling the function directly.
    async def fake_add_executor_job(func, *args, **kwargs):
        return func(*args, **kwargs)

    hass.async_add_executor_job = fake_add_executor_job
    return hass


def create_fake_config_entry(
    domain="muslim_prayer_companion", options=None, entry_id="test123"
):
    """Return a fake ConfigEntry with given options."""
    if options is None:
        options = {}
    entry = MagicMock()
    entry.domain = domain
    entry.options = options
    entry.entry_id = entry_id
    return entry


def dummy_prayer_times():
    """
    Return dummy prayer times as expected from get_new_prayer_times.
    Times are provided in HH:MM format.
    """
    return {
        "Fajr": "05:00",
        "Sunrise": "06:30",
        "Dhuhr": "12:00",
        "Asr": "15:30",
        "Maghrib": "18:00",
        "Isha": "19:30",
        "Midnight": "00:00",
    }


def dummy_hijri_date():
    """Return dummy Hijri date information."""
    return {
        "hijri_date": "10-09-1444",
        "hijri_day": "10",
        "hijri_month_num": 9,
        "hijri_month_readable": "Ramadan",
        "hijri_year": "1444",
        "hijri_date_readable": "10-Ramadan-1444",
        "hijri_day_month_readable": "10-Ramadan",
    }
