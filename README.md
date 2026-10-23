# StockTrack

A simple inventory tracker for small shops. Built with Python, Flask and SQLite.

## Features (MVP)
1. Secure login for the shop owner
2. Add, edit and delete items (name, category, price, quantity)
3. Search and filter the item list
4. Low-stock alerts based on a limit set per item
5. Summary page with total items and items to restock

## Run locally
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Default login: **owner** / **stocktrack123**
Change it with environment variables before real use:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Session signing key (set a long random value) |
| `OWNER_USERNAME` | Owner username |
| `OWNER_PASSWORD` | Owner password |
| `DATABASE` | Path to the SQLite file (default `stocktrack.db`) |

## Run the tests
```bash
pytest
```

## Deploy on Render (free plan)
1. Push this folder to GitHub.
2. On Render, create a **New Web Service** and connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add the environment variables above (`SECRET_KEY`, `OWNER_USERNAME`, `OWNER_PASSWORD`).

Note: free hosting may reset the SQLite file when the service restarts. Fine for a demo; for real use, attach a persistent disk and point `DATABASE` to it.

## Deploy on PythonAnywhere
Upload the files, create a virtualenv, `pip install -r requirements.txt`, then point the WSGI file at `from app import app as application` and set the environment variables.

## Known limits / future work
Barcode scanning, sales tracking, multiple staff accounts, supplier management, Excel export and a mobile app are not included.
