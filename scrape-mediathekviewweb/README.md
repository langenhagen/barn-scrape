# Scrape mediathekviewweb.de
Bulk-download media from mediathekviewweb.de for German public regulated / GEZ media.

The script uses the formidable project mediathekviewweb.de, based on
https://github.com/mediathekview/mediathekviewweb.


## Setup
Set up a Python virtual environment and install the requirements.
E.g., run:
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run
Run the script in the virtual environment you created when you set the project up.
Provide the URL that matches your search on https://mediathekviewweb.de.
E.g., run:
```bash
source .venv/bin/activate
python scrape-mediathekviewweb.py https://mediathekviewweb.de/#query=die%20biene%maja
```
