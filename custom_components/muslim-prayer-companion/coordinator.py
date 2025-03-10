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


# Convert a list of hour/minutes of a prayer to time in format 01:07.
# Inputs:
#   timelist: [hour Integer, Minutes Integer]
#   offset: +/- Integer of hour offset correction
# Outputs:
#   Time in format: HH:MM
def formatTime(timeList, offset):
    return str(timeList[0] + offset).zfill(2) + ":" + str(timeList[1]).zfill(2)


# convert time strin in fromat 05:08 to time list [5, 8]


def get_time_list(str_time):
    time_list = str_time.split(":")
    return [int(num) for num in time_list]


# Return Maghrib time & Midnight time for given latitude, longitude & calculation
# method.
# Inputs:
#   None
# Output:
#   Arg1: Maghrib time
#   Arg2: Midnight time
#   Arg3: Full Standard Prayers


def get_stand_sunset_midnight(latitude, longitude, calculation_method):
    # Only set midnight to 00:00, if failed to get the value via ISNA
    # standard calculation
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
        # LOGGER.info("ISNA Prayers: " + str(std_prayers) + " " + str(type(std_prayers)))
        midnight = std_prayers["Midnight"]
        LOGGER.info("Midnight from ISNA calculation: " + midnight)

        # As ICCI timetable may consider DST time from 1st of April to
        # end of October, and it supposed to start of last Sunday in
        # March, and end last Sunday of October. There is a few days
        # at end of March/October will be shift +/-1 hour.
        # Maghrib is consider same for all calculation, so will try to
        # compare ICCI with ISNA ones, and use that offset to fix all.
        # Prayers.
        maghrib = std_prayers["Maghrib"]
        LOGGER.info("Maghrib from ISNA calculation: " + maghrib)
    except Exception as e:
        LOGGER.info(
            "Failed to extract midnight/maghrib from ISNA calculation: " + str(e)
        )
    return maghrib, midnight, std_prayers


# Return json response from http request


def get_json_resp(url):
    json_resp = None
    try:
        resp = requests.get(url=url, params={})
        if resp.status_code != requests.codes.ok:
            LOGGER.debug(url + " : request failed")
        else:
            LOGGER.debug(url + ": ok")
            json_resp = resp.json()
    except Exception as e:
        LOGGER.info(url + " : request exception raised, got error: " + str(e))
    return json_resp


# There is a known bug with the Irish calculation for prayers, which consider DST
# start from start of APril till end of October, instead of last Sunday in March to
# last Sunday in October in Ireland.
# This function will compare the prayer between the standard and irish one, and will
# give the fix offset for the broken week at the start and end of the DST.
# It is prefer to use the Maghrib prayer, as Sunset is same in all calculation.
# Inputs:
#   non_stand_str: str with time format HH:MM
#   stand_str: str with time format HH:MM
# Outputs:
#   hr_offset: Int with +/- number of hours to offset


def get_hr_offset_fix(non_stand_str, stand_str):
    try:
        # Get different between standard/non-standard Mahrib ign seconds
        non_stand = datetime.strptime(non_stand_str, "%H:%M")
        stand = datetime.strptime(stand_str, "%H:%M")
    except Exception as e:
        LOGGER.info("Failed to parse time expecting HH:MM format: " + str(e))
        return 0

    hr_offset = 0
    delta = 0
    # if you subtract the bigger timestamp from smaller, you will get one day of seconds
    if non_stand > stand:
        delta = (non_stand - stand).seconds
        if delta > 900:
            hr_offset = -1
    if non_stand <= stand:
        delta = (stand - non_stand).seconds
        if delta > 900:
            hr_offset = 1
    LOGGER.info("DST offset fix in hours: " + str(hr_offset))
    return hr_offset


# getPrayersByWPPlugin gets the prayers from a WordPress site with the
# Daily Prayer Time plugin: https://wordpress.org/plugins/daily-prayer-time-for-mosques/
# This is used by mcnd.ie & hicc.ie


def getPrayersByWPPlugin(url, name, st_maghrib, midnight):
    json_resp = get_json_resp(url)
    LOGGER.debug(json_resp)
    if json_resp is not None:
        try:
            wp_prayers = json_resp[0]
            wp_fajr = get_time_list(wp_prayers["fajr_begins"][0:5])
            wp_sunrise = get_time_list(wp_prayers["sunrise"][0:5])
            wp_dhuhr = get_time_list(wp_prayers["zuhr_begins"][0:5])
            wp_asr = get_time_list(wp_prayers["asr_mithl_1"][0:5])
            wp_maghrib = get_time_list(wp_prayers["maghrib_begins"][0:5])
            wp_isha = get_time_list(wp_prayers["isha_begins"][0:5])

            # get fixed offset
            hr_offset = get_hr_offset_fix(wp_prayers["maghrib_begins"][0:5], st_maghrib)

            prayer_times_info = {
                "Fajr": formatTime(wp_fajr, hr_offset),
                "Sunrise": formatTime(wp_sunrise, hr_offset),
                "Dhuhr": formatTime(wp_dhuhr, hr_offset),
                "Asr": formatTime(wp_asr, hr_offset),
                "Sunset": formatTime(wp_maghrib, hr_offset),
                "Maghrib": formatTime(wp_maghrib, hr_offset),
                "Isha": formatTime(wp_isha, hr_offset),
                "Imsak": formatTime(wp_maghrib, hr_offset),
                "Midnight": midnight,
            }

            LOGGER.info(prayer_times_info)
            return prayer_times_info
        except Exception as e:
            LOGGER.info(
                "Failed to retrieve prayer from "
                + name
                + ", failed to parse prayers from JSON: "
                + str(e)
            )
            return None


class MuslimPrayerCompanionDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, datetime]]
):
    """Islamic Prayer Client Object."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the Muslim Prayer client."""

        self.event_unsub: CALLBACK_TYPE | None = None
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            # Update interval set to 30 minutes
            update_interval=timedelta(minutes=60),
        )

    @property
    def calc_method(self) -> str:
        """Return the calculation method."""
        return self.config_entry.options.get(CONF_CALC_METHOD, DEFAULT_CALC_METHOD)

    def get_new_prayer_times(self) -> dict[str, str]:
        """Fetch prayer times for today."""

        calc_method = self.calc_method
        LOGGER.debug(calc_method)

        # For Irish ICC calculation, we get the fill timetable of the year from
        # https://islamireland.ie/api/timetable/ , and parse JSON
        if calc_method == "ie-icci":
            st_maghrib, midnight, isna_prayers = get_stand_sunset_midnight(
                self.hass.config.latitude, self.hass.config.longitude, "isna"
            )

            current_month = datetime.today().strftime("%-m")
            current_day = datetime.today().strftime("%-d")
            url = "https://islamireland.ie/api/timetable/"
            json_resp = get_json_resp(url)
            LOGGER.debug(json_resp)
            if json_resp is not None:
                try:
                    prayers = json_resp["timetable"][current_month][current_day]
                    icci_maghrib = formatTime(prayers[4], 0)
                    LOGGER.info("Maghrib from ICCI calculation: " + icci_maghrib)

                    hr_offset = get_hr_offset_fix(icci_maghrib, st_maghrib)

                    prayer_times_info = {
                        "Fajr": formatTime(prayers[0], hr_offset),
                        "Sunrise": formatTime(prayers[1], hr_offset),
                        "Dhuhr": formatTime(prayers[2], hr_offset),
                        "Asr": formatTime(prayers[3], hr_offset),
                        "Sunset": formatTime(prayers[4], hr_offset),
                        "Maghrib": formatTime(prayers[4], hr_offset),
                        "Isha": formatTime(prayers[5], hr_offset),
                        "Imsak": formatTime(prayers[4], hr_offset),
                        "Midnight": midnight,
                    }

                    LOGGER.info(prayer_times_info)
                    return prayer_times_info
                except Exception as e:
                    LOGGER.info(
                        "Failed to retrive prayer from ICCI, failed to parse prayers from JSON: "
                        + str(e)
                    )
                    return isna_prayers
            else:
                LOGGER.info(
                    "Failed to retrive prayer from ICCI, JSON response is None."
                )
                return isna_prayers
        # For Masjid that use WordPress Daily Prayer Time plugin
        elif calc_method == "ie-mcnd" or calc_method == "ie-hicc":
            st_maghrib, midnight, isna_prayers = get_stand_sunset_midnight(
                self.hass.config.latitude, self.hass.config.longitude, "isna"
            )

            url = "https://mcnd.ie/wp-json/dpt/v1/prayertime?mcnd.ie/wp-json/dpt/v1/prayertime&filter=today"
            if calc_method == "ie-hicc":
                url = "https://hicc.ie/wp-json/dpt/v1/prayertime?mcnd.ie/wp-json/dpt/v1/prayertime&filter=today"
            prayer_times_info = getPrayersByWPPlugin(
                url, calc_method, st_maghrib, midnight
            )
            if prayer_times_info is None:
                return isna_prayers
            else:
                return prayer_times_info

        # For standard calculation methods, we use fetch_prayer_times library
        # resp is Dict, sample: {'Fajr': '06:47', 'Sunrise': '08:37', 'Dhuhr': '12:22', 'Asr': '13:53', 'Sunset': '16:07', 'Maghrib': '16:07', 'Isha': '17:57', 'Imsak': '06:37', 'Midnight': '00:22'}
        else:
            calc = PrayerTimesCalculator(
                latitude=self.hass.config.latitude,
                longitude=self.hass.config.longitude,
                calculation_method=self.calc_method,
                date=str(dt_util.now().date()),
            )
            return calc.fetch_prayer_times()

    @callback
    def async_schedule_future_update(self, midnight_dt: datetime) -> None:
        """Schedule future update for sensors.
        Midnight is a calculated time.  The specifics of the calculation
        depends on the method of the prayer time calculation.  This calculated
        midnight is the time at which the time to pray the Isha prayers have
        expired.
        Calculated Midnight: The Islamic midnight.
        Traditional Midnight: 12:00AM
        Update logic for prayer times:
        If the Calculated Midnight is before the traditional midnight then wait
        until the traditional midnight to run the update.  This way the day
        will have changed over and we don't need to do any fancy calculations.
        If the Calculated Midnight is after the traditional midnight, then wait
        until after the calculated Midnight.  We don't want to update the prayer
        times too early or else the timings might be incorrect.
        Example:
        calculated midnight = 11:23PM (before traditional midnight)
        Update time: 12:00AM
        calculated midnight = 1:35AM (after traditional midnight)
        update time: 1:36AM.
        """
        LOGGER.debug("Scheduling next update for Muslim Prayer Companion")

        now = dt_util.utcnow()

        if now > midnight_dt:
            next_update_at = midnight_dt + timedelta(days=1, minutes=1)
            LOGGER.debug(
                "Midnight is after the day changes so schedule update for after Midnight the next day"
            )
        else:
            LOGGER.debug(
                "Midnight is before the day changes so schedule update for the next start of day"
            )
            next_update_at = dt_util.start_of_local_day(now + timedelta(days=1))

        LOGGER.debug("Next update scheduled for: %s", next_update_at)

        self.event_unsub = async_track_point_in_time(
            self.hass, self.async_request_update, next_update_at
        )

    async def async_request_update(self, *_) -> None:
        """Request update from coordinator."""
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, datetime]:
        """Update sensors with new prayer times."""
        try:
            prayer_times = await self.hass.async_add_executor_job(
                self.get_new_prayer_times
            )
        except (exceptions.InvalidResponseError, ConnError) as err:
            async_call_later(self.hass, 60, self.async_request_update)
            raise UpdateFailed from err

        prayer_times_info: dict[str, datetime] = {}
        for prayer, time in prayer_times.items():
            if prayer_time := dt_util.parse_datetime(f"{dt_util.now().date()} {time}"):
                prayer_times_info[prayer] = dt_util.as_utc(prayer_time)

        self.async_schedule_future_update(prayer_times_info["Midnight"])
        return prayer_times_info
