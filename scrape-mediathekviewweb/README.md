# Scrape mediathekviewweb.de
Bulk-download media from mediathekviewweb.de for German public regulated / GEZ media.

The script uses the formidable project mediathekviewweb.de, based on
https://github.com/mediathekview/mediathekviewweb.


## Setup
Install the dependencies with [uv](https://docs.astral.sh/uv/):
```bash
uv sync
```

## Run
Provide the URL that matches your search on https://mediathekviewweb.de.
E.g., run:
```bash
uv run scrape-mediathekviewweb.py https://mediathekviewweb.de/#query=die%20biene%maja
```
