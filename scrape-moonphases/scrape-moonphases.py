#!/usr/bin/env python3
"""Scrape Info about the moon from www.heute-am-himmel.de.

author: andreasl
"""

import datetime as dt
import locale
from contextlib import suppress
from io import StringIO

import lxml.etree
import requests


def generate_friday_saturday_dates() -> list[dt.date]:
    """Generate dates for each Friday and Saturday in the current year."""
    year = dt.date.today().year
    start_date = dt.date(year, 1, 1)
    end_date = dt.date(year, 12, 31)

    # get all dates between start_date and end_date
    dates = [
        (start_date + dt.timedelta(days=i))
        for i in range((end_date - start_date).days + 1)
    ]

    # keep only Fridays and Saturdays
    dates = [d for d in dates if d.weekday() in {4, 5}]
    return dates


def get_moonrise_and_moonset(date: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
    """Retrieve moonrise and moonset times from heute-am-himmel.de
    via pages like https://www.heute-am-himmel.de/mond?date=2025-02-03.

    For dates where the moon is not visible at all, moonrise and moonset values
    are given date with times set to 0:0 for moonset and 23:59 for moonrise.
    """

    url = f"https://www.heute-am-himmel.de/mond?date={date.strftime('%Y-%m-%d')}"
    response = requests.get(url)
    response.raise_for_status()

    # Caution: the xpath items here don't use the `table/tbody` paths as
    # Google Chrome gives them out; rather, here, only `table/` gets used,
    # otherwise, lxml does not find a thing under `[...]/table/tbody/`.
    moonrise_xpath = "/html/body/div/div/main/div[3]/div[1]/table/tr[2]/td"
    moonset_xpath = "/html/body/div/div/main/div[3]/div[1]/table/tr[3]/td"

    tree = lxml.etree.parse(StringIO(response.text), lxml.etree.HTMLParser())

    # results look like: "Fr, 03.01.2025 20:10 Uhr" note the German locale
    # and the "Uhr" at the end
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")

    try:
        moonrise_result: str = tree.xpath(moonrise_xpath)[0].text
        moonset_result: str = tree.xpath(moonset_xpath)[0].text
        moonrise = dt.datetime.strptime(moonrise_result[:-4], "%a, %d.%m.%Y %H:%M")
        moonset = dt.datetime.strptime(moonset_result[:-4], "%a, %d.%m.%Y %H:%M")

    except Exception:
        result: str = tree.xpath("/html/body/div/div/main/div[3]/p")[0].text.strip()
        if result != "Der Mond ist leider nicht beobachtbar.":
            raise
        moonrise = dt.datetime.combine(date, dt.time(23, 59))
        moonset = dt.datetime.combine(date, dt.time(0, 0))

    return moonrise, moonset


def filter_moon_visibility(
    date_min: dt.datetime,
    date_max: dt.datetime,
    moonrise: dt.datetime,
    moonset: dt.datetime,
) -> bool:
    """Return True if the moon is NOT visible between date_min and date_max.

    Criteria:
    - Moonrise is after date_max -> Moon hasn't risen yet in the period.
    - Moonset is before date_min -> Moon has already set before the period.
    """
    return moonrise > date_max or moonset < date_min


def find_dates_when_moon_is_not_visible() -> None:
    """Find dates on the weekends when the moon is not visible in Germany"""

    min_time = dt.time(19, 0)
    max_time = dt.time(22, 0)

    print(f"Moon is not visible between {min_time} and {max_time} on following dates:\n")

    for date in generate_friday_saturday_dates():
        moonrise, moonset = get_moonrise_and_moonset(date)

        date_min = dt.datetime.combine(date, min_time)
        date_max = dt.datetime.combine(date, max_time)

        if moonrise > date_max or moonset < date_min:
            formatted = date.strftime("%A, %d.%m.%Y")
            print(f"{date}\t\t{formatted}")


def main() -> None:
    """Program main entry point."""
    find_dates_when_moon_is_not_visible()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        main()
