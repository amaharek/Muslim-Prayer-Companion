"""Config flow for Muslim Prayer Companion integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CALC_METHODS,
    DEFAULT_CALC_METHOD,
    DEFAULT_IQAMAH_METHOD,
    DEFAULT_IQAMAH_OFFSETS,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("calculation_method", default=DEFAULT_CALC_METHOD): vol.In(CALC_METHODS),
        # vol.Required("iqamah_method", default=DEFAULT_IQAMAH_METHOD): vol.In(["offset", "api"]),
        # For offset-based iqamah, expect a mapping for each prayer. Offsets in minutes.
        # vol.Optional("iqamah_offsets", default=DEFAULT_IQAMAH_OFFSETS): {
        #     vol.Optional("Fajr", default=DEFAULT_IQAMAH_OFFSETS["Fajr"]): vol.Coerce(int),
        #     vol.Optional("Dhuhr", default=DEFAULT_IQAMAH_OFFSETS["Dhuhr"]): vol.Coerce(int),
        #     vol.Optional("Asr", default=DEFAULT_IQAMAH_OFFSETS["Asr"]): vol.Coerce(int),
        #     vol.Optional("Maghrib", default=DEFAULT_IQAMAH_OFFSETS["Maghrib"]): vol.Coerce(int),
        #     vol.Optional("Isha", default=DEFAULT_IQAMAH_OFFSETS["Isha"]): vol.Coerce(int),
        # },
        # Optionally allow user to override API endpoints if using API-based methods.
        # vol.Optional("custom_prayer_api"): str,
        # vol.Optional("custom_iqamah_api"): str,
    }
)

class MuslimPrayerCompanionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Muslim Prayer Companion."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # In a real integration, validate the API endpoints if provided.
            return self.async_create_entry(title="Muslim Prayer Companion", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )