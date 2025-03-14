"""Platform to retrieve Muslim Prayer Companion information for Home Assistant."""
from datetime import datetime
from logging import getLogger

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime

from . import MuslimPrayerCompanionDataUpdateCoordinator
from .const import DOMAIN, NAME

_LOGGER = getLogger(__package__)
SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    # Prayer Times
    SensorEntityDescription(key="Fajr", name="Fajr Prayer", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="Sunrise", name="Sunrise Time", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="Dhuhr", name="Dhuhr Prayer", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="Asr", name="Asr Prayer", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="Maghrib", name="Maghrib Prayer", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="Isha", name="Isha Prayer", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="Midnight", name="Midnight Time", device_class=SensorDeviceClass.TIMESTAMP),
    # Hijri Date Information
    SensorEntityDescription(key="hijri_date", name="Hijri Date"),
    SensorEntityDescription(key="hijri_day", name="Hijri Day"),
    SensorEntityDescription(key="hijri_month_num", name="Hijri Month Number"),
    SensorEntityDescription(key="hijri_month_readable", name="Hijri Month"),
    SensorEntityDescription(key="hijri_year", name="Hijri Year"),
    SensorEntityDescription(key="hijri_date_readable", name="Hijri Date Readable"),
    SensorEntityDescription(key="hijri_day_month_readable", name="Hijri Day and Month"),
    # Iqamah Times
    SensorEntityDescription(key="iqamah_Fajr", name="Iqamah Fajr", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="iqamah_Dhuhr", name="Iqamah Dhuhr", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="iqamah_Asr", name="Iqamah Asr", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="iqamah_Maghrib", name="Iqamah Maghrib", device_class=SensorDeviceClass.TIMESTAMP),
    SensorEntityDescription(key="iqamah_Isha", name="Iqamah Isha", device_class=SensorDeviceClass.TIMESTAMP),
    # Next Prayer Sensor
    SensorEntityDescription(key="next_prayer", name="Next Prayer", device_class=SensorDeviceClass.TIMESTAMP),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up the Muslim Prayer Companion sensor platform.
    """
    coordinator: MuslimPrayerCompanionDataUpdateCoordinator = hass.data[DOMAIN]
    async_add_entities(
        MuslimPrayerCompanionTimeSensor(coordinator, description)
        for description in SENSOR_TYPES
    )

class MuslimPrayerCompanionTimeSensor(
    CoordinatorEntity[MuslimPrayerCompanionDataUpdateCoordinator], SensorEntity
):
    """Representation of a Muslim Prayer Companion sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MuslimPrayerCompanionDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{description.key}_{coordinator.config_entry.entry_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=NAME,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            _LOGGER.error("No value found for %s", self.entity_description.key)
            return None

        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            try:
                # Ensure value is a datetime object
                if isinstance(value, datetime):
                    return value  # Home Assistant handles datetime correctly

                # If it's a string, parse it
                elif isinstance(value, str):
                    return parse_datetime(value)

                else:
                    _LOGGER.error("Unexpected type for %s: %s", self.entity_description.key, type(value))
                    return None
            except Exception as e:
                _LOGGER.error("Error parsing datetime for %s: %s", self.entity_description.key, e)
                return None

        return value

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes for the sensor."""
        attrs = {}
        # For the "next_prayer" sensor, add the prayer name.
        if self.entity_description.key == "next_prayer":
            next_prayer_name = self.coordinator.data.get("next_prayer_name")
            if next_prayer_name:
                attrs["prayer"] = next_prayer_name
        return attrs