#!/usr/bin/env python3
"""Run predefined search queries against ebay kleinanzeigen in a loop
and notify per pushover in case a new match comes up."""
import io
import logging
import time
from typing import Set

import lxml.etree
import requests
import urllib3

logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%a %b %d %T %Y",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def send_pushover(message: str):
    """Send a push notification with the given message
    via the service `pushover.net`."""
    data = {
        "message": message,
        "token": "agna4fob6wu7e7t2ofhz1drt7ptngq",
        "user": "ucw67xi5r5mqgqo8arh3p64xkj39wu",
    }
    try:
        return requests.post("https://api.pushover.net/1/messages.json", data)
    except urllib3.exceptions.MaxRetryError:
        logger.error("Post to pushover encountered MaxRetryError. Giving up.")


def process_results(html: str, visited_links: Set[int]):
    """Inspect links on ebay kleinanzeigen search result page,
    check if the hash of the link is already in the set `visited_links`,
    add the hash of the link to `visited_links`
    and send a push notification."""
    tree = lxml.etree.parse(io.StringIO(html), lxml.etree.HTMLParser())
    results: list = tree.xpath('//*[@id="srchrslt-adtable"]/li[*]/article')

    logger.debug(f"{len(results)=}")
    for result in results:
        link = result.get("data-href")
        try:
            price = result.xpath(
                './/*[@class="aditem-main--middle--price-shipping--price"]'
            )[0].text.strip()
        except Exception:
            logger.exception(
                "Found no price tag on " f"https://www.kleinanzeigen.de{link}"
            )
            send_pushover(
                "Exception: found no price tag on: "
                f"https://www.ebay-kleinanzeigen.de{link}"
            )
            continue

        logger.debug(f"found https://www.ebay-kleinanzeigen.de{link} for {price=}")
        link_hash = hash(link)
        if link_hash in visited_links:
            continue
        visited_links.add(link_hash)

        send_pushover(
            f"Check out https://www.ebay-kleinanzeigen.de{link}\n" f"it's {price}"
        )

    logger.debug("that's all for this round")


def heartbeat():
    """Log hourly output to stdout."""
    global last_hour
    hour = time.localtime().tm_hour
    if "last_hour" not in globals() or hour != last_hour:
        logger.info("heartbeat")
    last_hour = hour


def handle_http_error(error_timestamps: Set[float]):
    """Checks if there were several errors within the 30 minutes and if yes, log
    a message and send a push notification."""
    half_hour_ago = time.time() - 1800
    recents = [ts for ts in error_timestamps if ts > half_hour_ago]
    n_errors = len(recents)
    if n_errors > 2:
        msg = f"Scrape Kleinanzeigen received {n_errors} http errors within the last 30 minutes"
        send_pushover(msg)
        logger.error(msg)

    error_timestamps.clear()
    error_timestamps.update(recents)


def main():
    """Query some ebay kleinanzeigen searches and process the results."""
    prefix = "https://www.ebay-kleinanzeigen.de/s-berlin/anzeige:angebote"
    urls = [
        f"{prefix}/preis:100:220/samsung-galaxy-s21/k0l3331",
        f"{prefix}/preis:100:250/samsung-galaxy-s22/k0l3331",
        f"{prefix}/preis:100:260/samsung-galaxy-s23/k0l3331",
        f"{prefix}/preis:1:20/star-wars-hot-wheels/k0l3331",
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
        for url in urls:
            try:
                response = requests.get(url, headers=headers)
            except urllib3.exceptions.MaxRetryError:
                logger.error("HTTP GET encountered MaxRetryError. Giving up.")
            else:
                if response.ok:
                    process_results(response.text, visited_links)
                else:
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
