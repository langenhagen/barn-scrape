#!/usr/bin/env python3
"""
Scrape video playlists from https://serversforhackers.com
and convert them to a *.m3u playlist.

The site serversforhackers.com is great but I wanted to be able to stream the
videos as a playlist on my chromecast.

Usage:
Call the script with a root url which contains a playlist. E.g., call:
  scrape-serversforhackers-com.py 'https://serversforhackers.com/s/start-here'
"""
import json
import os
import sys
from typing import List, Tuple

import bs4
import requests
import slugify


def get_soup(url: str):
    """Retrieve a Beautifulsoup object from an URL from a GET response."""
    response = requests.get(url)
    return bs4.BeautifulSoup(response.content, "html5lib")


def find_link_urls(soup, url_substring: str = "") -> List[str]:
    """Get all link URLs that contain the given substring from a given soup."""
    results = []
    for a in soup.find_all("a", href=True):
        link = a["href"]
        if url_substring in link:
            results.append(link)
    return results


def scrape_video_urls(url: str = "https://serversforhackers.com/s/start-here"):
    """
    Scrape the videos URLs from the given URL from serversforhackers.com
    and return the video page urls and corresponding video file urls.
    """
    page = get_soup(url)
    subpage_links_section = bs4.BeautifulSoup.find(
        page, "section", {"class": "bg-white py-10"}
    )
    subpage_urls = find_link_urls(
        subpage_links_section, "http://serversforhackers.com/c/"
    )
    video_urls = []
    for subpage_url in subpage_urls:
        video_page = get_soup(subpage_url)
        script = video_page.find("script", {"type": "application/ld+json"}).text
        video_url = json.loads(script, strict=False)["embedUrl"]
        print(video_url)
        video_urls.append(video_url)
    return video_urls, subpage_urls


def write_m3u(filepath: str, paths_and_names: List[Tuple[str, str]]):
    """
    Write given paths of media files with their according names to a
    *.m3u playlist file.
    *"""
    with open(filepath, "w+") as file:
        file.write("#EXTM3U\n")
        for path, name in paths_and_names:
            file.write(f"#EXTINF:0,{name}\n")
            file.write(f"{path}\n")


def run(url: str):
    """
    Scrape the videos URLs from the given URL from serversforhackers.com
    and write the videos to a *.m3u playlist file on the desktop.
    """
    filename = slugify.slugify(url)
    filepath = f"{os.environ['HOME']}/Desktop/{filename}.m3u"

    video_urls, videopage_urls = scrape_video_urls(url)
    assert len(video_urls) == len(videopage_urls)

    video_names = []
    prefix = "http://serversforhackers.com/c/"
    for i, videopage_url in enumerate(videopage_urls, 1):
        video_names.append(f"{i} {videopage_url[len(prefix):]}")

    video_paths_and_names = list(zip(video_urls, video_names))
    write_m3u(filepath, video_paths_and_names)


if __name__ == "__main__":
    run(sys.argv[1])
