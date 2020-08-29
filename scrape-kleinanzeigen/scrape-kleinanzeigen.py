#!/usr/env/bin python
"""Run predefined search queries against ebay kleinanzeigen in a loop
and notify per pushover in case a new match comes up."""
import io
import logging
import time
from typing import Set

import lxml.etree
import requests

logging.basicConfig(
    format='%(asctime)s [%(levelname)s]: %(message)s',
    datefmt="%a %b %d %H:%M:%S %Y",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def send_pushover(message: str):
    """Send a push notification with the given message
    via the service `pushover.net`."""
    data = {
        "message": message,
        "token": "agna4fob6wu7e7t2ofhz1drt7ptngq",
        "user": "ucw67xi5r5mqgqo8arh3p64xkj39wu"
    }
    return requests.post("https://api.pushover.net/1/messages.json", data)


def process_results(html: str, visited_links: Set[int]):
    """Inspect links on ebay kleinanzeigen search result page,
    check if the hash of the link is already in the set `visited_links`,
    add the hash of the link to `visited_links`
    and send a push notification."""
    tree = lxml.etree.parse(io.StringIO(html), lxml.etree.HTMLParser())
    results = tree.xpath('//*[@id="srchrslt-adtable"]/li[*]/article/div[2]/h2/a')
    for result in results:
        link = result.get("href")
        link_hash = hash(link)
        if link_hash in visited_links:
            continue
        visited_links.add(link_hash)
        send_pushover(f"Check out https://www.ebay-kleinanzeigen.de{link}")


def heartbeat():
    """Log hourly output to stdout."""
    global last_hour
    hour = time.localtime().tm_hour
    if 'last_hour' not in globals() or hour != last_hour:
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
        f"{prefix}/preis:100:170/croozer/k0l3331",
        f"{prefix}/preis:100:180/thule-chariot/k0l3331"]
    headers = {
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36")}
    visited_links = set()

    error_timestamps = set()

    while True:
        heartbeat()
        for url in urls:
            response = requests.get(url, headers=headers)
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
