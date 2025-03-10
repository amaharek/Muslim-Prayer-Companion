# Muslim-Prayer-Companion

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

Muslim Prayer Companion is a HACS component built to deliver precise prayer times tailored to your location. This integration allows you to seamlessly incorporate daily prayer schedules, including Iqamah and Jummah times, into your smart home setup, ensuring timely reminders and notifications for all five daily prayers.

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show prayer times information.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `muslim-prayer-companion`.
1. Download _all_ the files from the `custom_components/muslim-prayer-companion/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Muslim Prayer Companion".

## Configuration is done in the UI

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[muslim-prayer-companion]: https://github.com/amaharek/Muslim-Prayer-Companion
[buymecoffee]: https://www.buymeacoffee.com/amaharek
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/amaharek/Muslim-Prayer-Companion.svg?style=for-the-badge
[commits]: https://github.com/amaharek/Muslim-Prayer-Companion/commits/main
[license-shield]: https://img.shields.io/github/license/amaharek/Muslim-Prayer-Companion.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/amaharek/Muslim-Prayer-Companion.svg?style=for-the-badge
[releases]: https://github.com/amaharek/Muslim-Prayer-Companion/releases