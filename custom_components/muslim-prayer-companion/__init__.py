"""
Custom component to get Muslim Prayer Companion.

For more details about this component, please refer to the documentation at
https://github.com/amaharek/Muslim-Prayer-Companion
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import MuslimPrayerCompanionDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=False)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Islamic Prayer Component."""
    coordinator = MuslimPrayerCompanionDataUpdateCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, coordinator)
    config_entry.async_on_unload(config_entry.add_update_listener(async_options_updated))
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload Islamic Prayer entry from config_entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS):
        coordinator: MuslimPrayerCompanionDataUpdateCoordinator = hass.data.pop(DOMAIN)
        if coordinator.event_unsub:
            coordinator.event_unsub()
    return unload_ok


async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Triggered by config entry options updates."""
    coordinator: MuslimPrayerCompanionDataUpdateCoordinator = hass.data[DOMAIN]
    if coordinator.event_unsub:
        coordinator.event_unsub()
    await coordinator.async_request_refresh()
