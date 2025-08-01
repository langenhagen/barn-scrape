#!/usr/bin/env python3
"""Run predefined search queries against ebay kleinanzeigen in a loop
and notify per pushover in case a new match comes up.
"""

import logging
import re
import time
from dataclasses import dataclass
from io import StringIO
from typing import Optional

import lxml.etree
import requests
import urllib3


@dataclass
class SearchDetails:
    url: str
    negative_regex: Optional[str] = None  # discard thingy if matches


logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%a %b %d %T %Y",
    level=logging.INFO,
    # level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


def send_pushover(message: str):
    """Send a push notification with the given message
    via the service `pushover.net`.
    """
    data = {
        "message": message,
        "token": "agna4fob6wu7e7t2ofhz1drt7ptngq",
        "user": "ucw67xi5r5mqgqo8arh3p64xkj39wu",
    }
    try:
        return requests.post("https://api.pushover.net/1/messages.json", data)
    except urllib3.exceptions.MaxRetryError:
        logger.error("Post to pushover encountered MaxRetryError. Giving up.")


def process_results(
    html: str,
    negative_regex: Optional[str],
    visited_links: set[int],
) -> None:
    """Inspect links on Kleinanzeigen search result page,
    check if the negative regex matchies.
    If not, check if the hash of the link is already in the set `visited_links`,
    add the hash of the link to `visited_links`
    and send a push notification.
    """
    tree = lxml.etree.parse(StringIO(html), lxml.etree.HTMLParser())
    results: list = tree.xpath('//*[@id="srchrslt-adtable"]/li[*]/article')

    logger.debug(f"{len(results)=}")
    for result in results:
        link = result.get("data-href")
        if negative_regex and re.search(negative_regex, link, flags=re.IGNORECASE):
            continue

        try:
            price = result.xpath(
                './/*[@class="aditem-main--middle--price-shipping--price"]'
            )[0].text.strip()
        except Exception:
            logger.exception(
                "Found no price tag on https://www.kleinanzeigen.de%s", link
            )
            send_pushover(
                f"Exception: found no price tag on: https://www.kleinanzeigen.de{link}"
            )
            continue

        logger.debug("found https://www.kleinanzeigen.de%s for price=%d", link, price)
        link_hash = hash(link)
        if link_hash in visited_links:
            continue
        visited_links.add(link_hash)

        send_pushover(f"Check out https://www.kleinanzeigen.de{link}\nit's {price}")

    logger.debug("that's all for this round")


def heartbeat() -> None:
    """Log hourly output to stdout."""
    global last_hour
    hour = time.localtime().tm_hour
    if "last_hour" not in globals() or hour != last_hour:
        logger.info("heartbeat")
    last_hour = hour


def handle_http_error(error_timestamps: set[float]) -> None:
    """Check if there were several errors within the 30 minutes and if yes, log
    a message and send a push notification.
    """
    half_hour_ago = time.time() - 1800
    recents = [ts for ts in error_timestamps if ts > half_hour_ago]
    n_errors = len(recents)
    if n_errors > 2:
        msg = f"Scrape Kleinanzeigen received {n_errors} http errors within the last 30 minutes"
        send_pushover(msg)
        logger.error(msg)

    error_timestamps.clear()
    error_timestamps.update(recents)


def main() -> None:
    """Query some kleinanzeigen searches and process the results."""
    prefix = "https://www.kleinanzeigen.de/anzeige:angebote"
    searches = [
        # SearchDetails(
        #     f"{prefix}/preis:100:160/samsung-galaxy-s21/k0l3331",
        #     negative_regex="schaden|defekt|reparatur",
        # ),
        # SearchDetails(
        #     f"{prefix}/preis:100:200/samsung-galaxy-s22/k0l3331",
        #     negative_regex="schaden|defekt|reparatur",
        # ),
        # SearchDetails(
        #     f"{prefix}/preis:100:220/samsung-galaxy-s23/k0l3331",
        #     negative_regex="schaden|defekt|reparatur",
        # ),
        SearchDetails(f"{prefix}/preis:25:30/mario-kart-8-deluxe/k0l3331"),
    ]
    headers = {
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        )
    }
    visited_links = set()

    error_timestamps = set()

    while True:
        heartbeat()
        for search in searches:
            try:
                response = requests.get(search.url, headers=headers)
            except urllib3.exceptions.MaxRetryError:
                logger.error("HTTP GET encountered MaxRetryError. Giving up.")
            else:
                if response.ok:
                    process_results(
                        response.text,
                        negative_regex=search.negative_regex,
                        visited_links=visited_links,
                    )
                else:
                    logger.error(
                        "HTTP GET %s encountered error %d",
                        response.url,
                        response.status_code,
                    )
                    handle_http_error(error_timestamps)
                time.sleep(20)
        time.sleep(500)


if __name__ == "__main__":
    while True:
        logger.info("Scrape Kleinanzeigen starts")
        try:
            main()
        except Exception:
            logger.exception("Scrape Kleinanzeigen encountered an uncaught exception")
