#!/usr/bin/env python3
"""Scrape Music from https://downloads.khinsider.com/.

Creates the out dir if it doesn't exist.

E.g.:

    python scrape-video-game-music.py 'https://downloads.khinsider.com/game-soundtracks/album/minecraft' 'out-dir'

author: andreasl
"""

import sys
import time
from contextlib import suppress
from io import StringIO
from pathlib import Path
from urllib.parse import unquote, urljoin

import lxml.etree
import requests

headers = {
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    )
}


def format_size(num_bytes: int) -> str:
    """Format a byte count as a human-readable size, e.g. `3.1 MiB`."""
    size = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            return f"{size:.1f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def format_duration(seconds: float) -> str:
    """Format an elapsed duration, e.g. `48s` or `12m 04s`."""
    minutes, secs = divmod(int(seconds), 60)
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def download_song(song_url: str, out_dir: Path, index: int, total: int) -> int:
    """Download a song and return the number of bytes written."""
    filename = unquote(song_url.split("/")[-1])
    out_path = out_dir / filename

    resp = requests.get(song_url, headers=headers, stream=True)
    resp.raise_for_status()

    size = 0
    with out_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                size += f.write(chunk)

    counter = f"{index:>{len(str(total))}}/{total}"
    print(f"[{counter}] {filename}  ({format_size(size)})")
    return size


def scrape_song_page(song_page_url: str, out_dir: Path, index: int, total: int) -> int:
    """Scrape single song page, find audio source, and download song to given
    output dir. Return the number of bytes written.
    """
    resp = requests.get(song_page_url, headers=headers)
    resp.raise_for_status()
    page_tree = lxml.etree.parse(StringIO(resp.text), lxml.etree.HTMLParser())
    audio_elem = page_tree.xpath('//*[@id="audio"]')

    audio_src = audio_elem[0].attrib.get("src")
    return download_song(audio_src, out_dir, index, total)


def scrape_album_page(album_page_url: str, out_dir: Path) -> None:
    """Scrape given album page for song links and download all songs to given
    output dir.
    """

    response = requests.get(album_page_url, headers=headers)
    response.raise_for_status()

    # CAUTION: the xpath items here don't use the `table/tbody` paths as
    # Google Chrome gives them out; rather, here, only `table/` gets used,
    # otherwise, lxml does not find a thing under `[...]/table/tbody/`.
    tree = lxml.etree.parse(StringIO(response.text), lxml.etree.HTMLParser())
    xpath = "/html/body/div[1]/div[2]/div/table[2]/tr[*]/td[4]/a"
    link_to_song_page: list = tree.xpath(xpath)

    total = len(link_to_song_page)
    print(f"Downloading {total} tracks to {out_dir}\n")

    start = time.monotonic()
    total_bytes = 0
    for index, link in enumerate(link_to_song_page, 1):
        href = link.attrib.get("href")
        song_page_url = urljoin(album_page_url, href)
        total_bytes += scrape_song_page(song_page_url, out_dir, index, total)

    elapsed = format_duration(time.monotonic() - start)
    print(f"\nDone: {total} tracks, {format_size(total_bytes)} in {elapsed}")


def main() -> None:
    """Program main entry point."""

    if len(sys.argv) != 3:
        print(
            f"usage: {sys.argv[0]} <ALBUM_URL> <OUT_DIR> "
            "(OUT_DIR is created if missing)"
        )
        sys.exit(1)

    url = sys.argv[1]
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    scrape_album_page(url, out_dir)


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        main()
