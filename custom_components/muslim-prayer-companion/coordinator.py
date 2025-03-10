"""
Muslim Prayer Companion Coordinator
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import requests

from prayer_times_calculator import PrayerTimesCalculator, exceptions
from requests.exceptions import ConnectionError as ConnError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import CONF_CALC_METHOD, DEFAULT_CALC_METHOD
from .const import DOMAIN, LOGGER


def format_time(time_list, offset):
    """
    Convert a list of hour/minutes of a prayer to time in format HH:MM.

    Args:
        time_list (list): [hour, minute]
        offset (int): Hour offset correction

    Returns:
        str: Time in format HH:MM
    """
    return f"{str(time_list[0] + offset).zfill(2)}:{str(time_list[1]).zfill(2)}"


def get_time_list(str_time):
    """
    Convert time string in format HH:MM to time list [hour, minute].

    Args:
        str_time (str): Time string in format HH:MM

    Returns:
        list: [hour, minute]
    """
    return [int(num) for num in str_time.split(":")]


def get_standard_sunset_midnight(latitude, longitude, calculation_method):
    """
    Return Maghrib time & Midnight time for given latitude, longitude & calculation method.

    Args:
        latitude (float): Latitude
        longitude (float): Longitude
        calculation_method (str): Calculation method

    Returns:
        tuple: Maghrib time, Midnight time, Full Standard Prayers
    """
    midnight = "00:00"
    maghrib = ""
    try:
        calc = PrayerTimesCalculator(
            latitude=latitude,
            longitude=longitude,
            calculation_method=calculation_method,
            date=str(dt_util.now().date()),
        )
        std_prayers = calc.fetch_prayer_times()
        midnight = std_prayers["Midnight"]
        maghrib = std_prayers["Maghrib"]
    except Exception as e:
        LOGGER.info(
            f"Failed to extract midnight/maghrib from ISNA calculation: {e}")
    return maghrib, midnight, std_prayers


def get_json_response(url):
    """
    Return JSON response from HTTP request.

    Args:
        url (str): URL to fetch JSON from

    Returns:
        dict: JSON response
    """
    try:
        resp = requests.get(url=url)
        if resp.status_code == requests.codes.ok:
            return resp.json()
        else:
            LOGGER.debug(f"{url} : request failed")
    except Exception as e:
        LOGGER.info(f"{url} : request exception raised, got error: {e}")
    return None


def get_hour_offset_fix(non_standard_str, standard_str):
    """
    Compare the prayer between the standard and non-standard one, and give the fix offset for the broken week at the start and end of the DST.

    Args:
        non_standard_str (str): Non-standard time in format HH:MM
        standard_str (str): Standard time in format HH:MM

    Returns:
        int: Hour offset
    """
    try:
        non_standard = datetime.strptime(non_standard_str, "%H:%M")
        standard = datetime.strptime(standard_str, "%H:%M")
    except Exception as e:
        LOGGER.info(f"Failed to parse time expecting HH:MM format: {e}")
        return 0

    delta = (non_standard - standard).seconds if non_standard > standard else (
        standard - non_standard).seconds
    return -1 if delta > 900 and non_standard > standard else 1 if delta > 900 else 0


def get_prayers_by_wp_plugin(url, name, standard_maghrib, midnight):
    """
    Get the prayers from a WordPress site with the Daily Prayer Time plugin.

    Args:
        url (str): URL to fetch prayers from
        name (str): Name of the calculation method
        standard_maghrib (str): Standard Maghrib time
        midnight (str): Midnight time

    Returns:
        dict: Prayer times information
    """
    json_resp = get_json_response(url)
    if json_resp:
        try:
            wp_prayers = json_resp[0]
            hr_offset = get_hour_offset_fix(
                wp_prayers["maghrib_begins"][0:5], standard_maghrib)
            prayer_times_info = {
                "Fajr": format_time(get_time_list(wp_prayers["fajr_begins"][0:5]), hr_offset),
                "Sunrise": format_time(get_time_list(wp_prayers["sunrise"][0:5]), hr_offset),
                "Dhuhr": format_time(get_time_list(wp_prayers["zuhr_begins"][0:5]), hr_offset),
                "Asr": format_time(get_time_list(wp_prayers["asr_mithl_1"][0:5]), hr_offset),
                "Sunset": format_time(get_time_list(wp_prayers["maghrib_begins"][0:5]), hr_offset),
                "Maghrib": format_time(get_time_list(wp_prayers["maghrib_begins"][0:5]), hr_offset),
                "Isha": format_time(get_time_list(wp_prayers["isha_begins"][0:5]), hr_offset),
                "Imsak": format_time(get_time_list(wp_prayers["maghrib_begins"][0:5]), hr_offset),
                "Midnight": midnight,
            }
            return prayer_times_info
        except Exception as e:
            LOGGER.info(
                f"Failed to retrieve prayer from {name}, failed to parse prayers from JSON: {e}")
    return None


class MuslimPrayerCompanionDataUpdateCoordinator(DataUpdateCoordinator[dict[str, datetime]]):
    """Islamic Prayer Client Object."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the Muslim Prayer client."""
        self.event_unsub: CALLBACK_TYPE | None = None
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=60),
        )

    @property
    def calc_method(self) -> str:
        """Return the calculation method."""
        return self.config_entry.options.get(CONF_CALC_METHOD, DEFAULT_CALC_METHOD)

    def get_hijri_date(self) -> dict[str, str]:
        """Fetch Hijri date."""
        calc = PrayerTimesCalculator(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            calculation_method=self.calc_method,
            date=str(dt_util.now().date()),
        )

        hijri_date = calc["data"]["hijri"]["date"] # DD-MM-YYYY
        hijri_day = calc["data"]["hijri"]["day"]
        hijri_month_num = calc["data"]["hijri"]["month"]["number"]
        hijri_month_readable = calc["data"]["hijri"]["month"]["en"]
        hijri_year = calc["data"]["hijri"]["year"] 
        hijri_day_month_readable = f"{hijri_day}-{hijri_month_readable}"
        hijri_date_readable = f"{hijri_day}-{hijri_month_readable}-{hijri_year}"
        
        data = {
            'hijri_date': hijri_date,
            'hijri_day': hijri_day,
            'hijri_month_num': hijri_month_num,
            'hijri_month_readable': hijri_month_readable,
            'hijri_year': hijri_year,
            'hijri_date_readable': hijri_date_readable,
            'hijri_day_month_readable': hijri_day_month_readable
        }

        return data

    def get_new_prayer_times(self) -> dict[str, str]:
        """Fetch prayer times for today."""
        calc_method = self.calc_method
        LOGGER.debug(calc_method)

        calculated_prayer_time = self._get_prayer_times_standard()

        if calc_method == "ie-icci":
            prayer_times = self._get_prayer_times_ie_icci()
        elif calc_method in ["ie-mcnd", "ie-hicc"]:
            prayer_times = self._get_prayer_times_wp_plugin(calc_method)
        else:
            prayer_times = calculated_prayer_time

        hijri_date = calculated_prayer_time['date']['hijri']['date'] # DD-MM-YYYY
        hijri_day = calculated_prayer_time['date']['hijri']['day']
        hijri_month_num = calculated_prayer_time['date']['hijri']['month']['number']
        hijri_month_readable = calculated_prayer_time['date']['hijri']['month']['en']
        hijri_year = calculated_prayer_time['date']['hijri']['year'] 
        hijri_day_month_readable = f"{hijri_day}-{hijri_month_readable}"
        hijri_date_readable = f"{hijri_day}-{hijri_month_readable}-{hijri_year}"

        data = {**prayer_times}
        data['hijri_date'] = hijri_date
        data['hijri_day'] = hijri_day
        data['hijri_month_num'] = hijri_month_num
        data['hijri_month_readable'] = hijri_month_readable
        data['hijri_year'] = hijri_year
        data['hijri_date_readable'] = hijri_date_readable
        data['hijri_day_month_readable'] = hijri_day_month_readable 
        

        return data

    def _get_prayer_times_ie_icci(self) -> dict[str, str]:
        """Fetch prayer times for 'ie-icci' calculation method."""
        st_maghrib, midnight, isna_prayers = get_standard_sunset_midnight(
            self.hass.config.latitude, self.hass.config.longitude, "isna"
        )
        url = "https://islamireland.ie/api/timetable/"
        json_resp = get_json_response(url)
        if json_resp:
            try:
                current_month = datetime.today().strftime("%-m")
                LOGGER.info(f"Current month: {current_month}")

                current_day = datetime.today().strftime("%-d")
                LOGGER.info(f"Current day: {current_day}")

                prayers = json_resp["timetable"][current_month][current_day]
                LOGGER.info(f"Prayers: {prayers}")

                icci_maghrib = format_time(prayers[4], 0)
                LOGGER.info(f"ICCI Maghrib: {icci_maghrib}")

                hr_offset = get_hour_offset_fix(icci_maghrib, st_maghrib)
                LOGGER.info(f"Hour offset: {hr_offset}")

                prayer_times_info = {
                    "Fajr": format_time(prayers[0], hr_offset),
                    "Sunrise": format_time(prayers[1], hr_offset),
                    "Dhuhr": format_time(prayers[2], hr_offset),
                    "Asr": format_time(prayers[3], hr_offset),
                    "Sunset": format_time(prayers[4], hr_offset),
                    "Maghrib": format_time(prayers[4], hr_offset),
                    "Isha": format_time(prayers[5], hr_offset),
                    "Imsak": format_time(prayers[4], hr_offset),
                    "Midnight": midnight,
                }
                LOGGER.info(f"Prayer times info: {prayer_times_info}")
                
                return prayer_times_info
            except Exception as e:
                LOGGER.info(f"Failed to retrieve prayer from ICCI, failed to parse prayers from JSON: {e}")
                return isna_prayers
        else:
            LOGGER.info("Failed to retrieve prayer from ICCI, JSON response is None.")
            return isna_prayers

    def _get_prayer_times_wp_plugin(self, calc_method: str) -> dict[str, str]:
        """Fetch prayer times for WordPress plugin calculation methods."""
        st_maghrib, midnight, isna_prayers = get_standard_sunset_midnight(
            self.hass.config.latitude, self.hass.config.longitude, "isna"
        )
        url = f"https://{calc_method.split('-')[1]}.ie/wp-json/dpt/v1/prayertime?filter=today"
        prayer_times_info = get_prayers_by_wp_plugin(url, calc_method, st_maghrib, midnight)
        return prayer_times_info if prayer_times_info else isna_prayers

    def _get_prayer_times_standard(self) -> dict[str, str]:
        """Fetch prayer times for standard calculation methods."""
        calc = PrayerTimesCalculator(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            calculation_method="isna",
            date=str(dt_util.now().date()),
        )
        return calc.fetch_prayer_times()

    @callback
    def async_schedule_future_update(self, midnight_dt: datetime) -> None:
        """
        Schedule future update for sensors.

        Midnight is a calculated time. The specifics of the calculation depend on the method of the prayer time calculation.
        This calculated midnight is the time at which the time to pray the Isha prayers have expired.

        Args:
            midnight_dt (datetime): Calculated midnight time
        """
        LOGGER.debug("Scheduling next update for Muslim Prayer Companion")

        now = dt_util.utcnow()
        next_update_at = midnight_dt + \
            timedelta(days=1, minutes=1) if now > midnight_dt else dt_util.start_of_local_day(
                now + timedelta(days=1))

        LOGGER.debug(f"Next update scheduled for: {next_update_at}")

        self.event_unsub = async_track_point_in_time(
            self.hass, self.async_request_update, next_update_at
        )

    async def async_request_update(self, *_) -> None:
        """Request update from coordinator."""
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, datetime]:
        """Update sensors with new prayer times."""
        try:
            prayer_times = await self.hass.async_add_executor_job(self.get_new_prayer_times)
            hijri_date = await self.hass.async_add_executor_job(self.get_hijri_date)

        except (exceptions.InvalidResponseError, ConnError) as err:
            async_call_later(self.hass, 60, self.async_request_update)
            raise UpdateFailed from err


        prayer_times_info = {prayer: dt_util.as_utc(dt_util.parse_datetime(
            f"{dt_util.now().date()} {time}")) for prayer, time in prayer_times.items()}
        hijri_date_info = {key: value for key, value in hijri_date.items()}
        

        self.async_schedule_future_update(prayer_times_info["Midnight"])
        return {**prayer_times_info, **hijri_date_info}