# Scrape Kleinanzeigen
Regularly run predefined search queries on eBay Kleinanzeigen and receive push notifications.

The script includes some timeouts in order to avoid eBay Kleinanzeigen blocking your IP address for
misusing their service.


## Setup
Set up a Python virtual environment and install the requirements.
E.g., run:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
Prior to running the script, review the code. Inspect and modify the search queries to your needs.

Run the script in the virtual environment you created when you set the project up.
E.g., run:
```bash
source .venv/bin/activate
python scrape-kleinanzeigen.py
```

You may want to run it via `nohup` and detach it from the shell. E.g. run:
```bash
source .venv/bin/activate
nohup python scrape-kleinanzeigen.py &
```
