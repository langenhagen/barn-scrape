#!/usr/env/bin python
"""Run predefined search queries against ebay kleinanzeigen in a loop
and notify per pushover in case a new match comes up."""
import io
import sys
import time
from typing import Set

import lxml.etree
import requests


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
        print(f"{time.asctime()} heartbeat")
        sys.stdout.flush()
    last_hour = hour


def main():
    """Query some ebay kleinanzeigen searches and process the results."""
    prefix = "https://www.ebay-kleinanzeigen.de/s-berlin/anzeige:angebote"
    urls = [
        f"{prefix}/preis:100:200/croozer/k0l3331",
        f"{prefix}/preis:100:250/thule-chariot/k0l3331"]
    headers = {
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36")}
    visited_links = set()

    while True:
        heartbeat()
        for url in urls:
            response = requests.get(url, headers=headers)
            if response.ok:
                process_results(response.text, visited_links)
            else:
                send_pushover("Scrape Kleinanzeigen received an http error")
                print("Scrape Kleinanzeigen received an http error")
            time.sleep(20)
        time.sleep(500)


if __name__ == "__main__":
    main()
