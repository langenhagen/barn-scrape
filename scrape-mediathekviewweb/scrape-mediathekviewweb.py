#!/usr/bin/env python
"""Request the given Feed-URL from mediathekviewweb.de and download all search
result videos.

Use like:

  ./scrape-mediathekviewweb.py 'https://mediathekviewweb.de/feed?query=drache kokosnuss&future=false'
"""
import datetime as dt
import logging
import pathlib
import sys

import dateutil.parser
import lxml.etree as etree
import requests
import slugify
import urllib3

logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%T %Y",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


def download_file(folder: pathlib.Path, filename: str, url: str):
    """Download the data from the given link to the file with the given name."""
    resp = requests.get(url, allow_redirects=True)
    resp.raise_for_status()
    open(folder / filename, "wb").write(resp.content)


def process_results(url: str, feed: bytes):
    """Inspect links on mediathekviewweb.de search result page,
    check if the hash of the link is already in the set `visited_links`,
    add the hash of the link to `visited_links`
    and send a push notification."""
    folder = pathlib.Path(slugify.slugify(url))
    folder.mkdir(parents=True, exist_ok=True)

    tree = etree.fromstring(feed)
    items = tree.xpath("//item")
    print(f"Downloading {len(items)} items...")
    for count, item in enumerate(items, 1):
        item_map = {}
        for element in item.getiterator():
            item_map[element.tag] = element.text

        log.info(f"{count}/{len(items)} Downloading {url}...")
        date = dateutil.parser.parse(item_map["pubDate"])
        date_str = dt.datetime.strftime(date, "%Y-%m-%d--%H-%M")
        filename = f"{date_str} - {item_map['title']}"
        download_file(folder, filename, item_map["link"])


def main(url: str):
    """Query a search at the given URL, a mediathekviewweb.de search rss feed
    URL, and download all results in the best quality."""

    try:
        response = requests.get(url)
    except urllib3.exceptions.MaxRetryError:
        log.error("HTTP GET encountered MaxRetryError. Giving up.")
    else:
        response.raise_for_status()
        process_results(url, response.content)


if __name__ == "__main__":

    if len(sys.argv) != 2:
        base = f"python {sys.argv[0]} 'https://mediathekviewweb.de/feed?query="
        print(f"Usage:\n  {base}<query>'\n")
        print(f"Example:\n  {base}die%20biene%20maja&future=false'")
        sys.exit(1)

    try:
        main(sys.argv[1])
    except Exception:
        log.exception("scrape-mediathekviewweb encountered an uncaught exception")
