# Muslim Companion

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

Muslim Prayer Companion is a HACS component built to deliver precise prayer times tailored to your location. This integration allows you to seamlessly incorporate daily prayer schedules, including Iqamah and Jummah times, into your smart home setup, ensuring timely reminders and notifications for all five daily prayers.

**This integration will set up the following platforms.**

| Platform | Description                    |
| -------- | ------------------------------ |
| `sensor` | Show prayer times information. |

## Installation

Using HACS add the repo, go to settings, integrations, add "Muslim prayer companion" choose calc method

## Configuration is done in the UI

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[muslim_prayer_companion]: https://github.com/amaharek/muslim_prayer_companion
[buymecoffee]: https://www.buymeacoffee.com/amaharek
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/amaharek/muslim_prayer_companion.svg?style=for-the-badge
[commits]: https://github.com/amaharek/muslim_prayer_companion/commits/main
[license-shield]: https://img.shields.io/github/license/amaharek/muslim_prayer_companion.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/amaharek/muslim_prayer_companion.svg?style=for-the-badge
[releases]: https://github.com/amaharek/muslim_prayer_companion/releases

```
poetry run pytest --cov custom_components/ tests/
poetry run pre-commit run --all-files
```
