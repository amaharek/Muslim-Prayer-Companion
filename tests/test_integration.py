"""
Test cases for the Muslim Prayer Companion integration.
These tests cover coordinator updates, sensor state conversion, and the config flow.
"""

from datetime import date, datetime, timedelta

import homeassistant.util.dt as dt_util
import pytest
from homeassistant.util.dt import as_utc
from test_helpers import (
    create_fake_config_entry,
    create_fake_hass,
    dummy_hijri_date,
    dummy_prayer_times,
)

# Import components from the integration.
from custom_components.muslim_prayer_companion import (
    config_flow,
    const,
    coordinator,
    sensor,
)


@pytest.fixture
def fake_hass():
    """Return a fake HomeAssistant instance."""
    return create_fake_hass()


@pytest.fixture
def fake_config_entry():
    """Return a fake ConfigEntry with default options."""
    options = {
        const.CONF_CALC_METHOD: const.DEFAULT_CALC_METHOD,
        const.CONF_IQAMAH_OFFSETS: const.DEFAULT_IQAMAH_OFFSETS,
        const.CONF_IQAMAH_METHOD: "offset",
    }
    return create_fake_config_entry(options=options)


@pytest.fixture
def coordinator_instance(fake_hass, fake_config_entry):
    """Instantiate the coordinator with fake hass and config entry."""
    coord = coordinator.MuslimPrayerCompanionDataUpdateCoordinator(fake_hass)
    coord.config_entry = fake_config_entry

    # Monkeypatch methods to return dummy data.
    coord.get_new_prayer_times = lambda: dummy_prayer_times()
    coord.get_hijri_date = lambda: dummy_hijri_date()
    return coord


@pytest.mark.asyncio
async def test_coordinator_update(coordinator_instance):
    """
    Test that the coordinator update returns a data dictionary containing:
    - Prayer times keys (Fajr, Sunrise, etc.)
    - Next prayer and next prayer name.
    """
    data = await coordinator_instance._async_update_data()
    # Check that all expected prayer time keys are present.
    for key in ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha", "Midnight"]:
        assert key in data, f"Missing key: {key}"

    # Verify that the next prayer information is set.
    assert "next_prayer" in data
    assert "next_prayer_name" in data


def test_sensor_native_value(coordinator_instance):
    """
    Test that the sensor entity returns a valid datetime object as native_value
    when the sensor is of device_class TIMESTAMP.
    """
    now = datetime.now()
    # Simulate a coordinator data value (using UTC for timestamps)
    coordinator_instance.data = {
        "Fajr": as_utc(now + timedelta(hours=1)),
    }
    # Create a sensor entity for the Fajr prayer.
    sensor_entity = sensor.MuslimPrayerCompanionTimeSensor(
        coordinator_instance, sensor.SENSOR_TYPES[0]
    )
    native_value = sensor_entity.native_value
    assert isinstance(native_value, datetime)


@pytest.mark.asyncio
async def test_config_flow(fake_hass):
    """
    Test the config flow by simulating a user step.
    The expected result is that an entry is created with the provided data.
    """
    flow = config_flow.MuslimPrayerCompanionConfigFlow()
    # Simulate a user input with the default calculation method.
    user_input = {"calculation_method": const.DEFAULT_CALC_METHOD}
    result = await flow.async_step_user(user_input)
    # The flow should create an entry.
    assert result["type"] == "create_entry"
    assert result["data"] == user_input
