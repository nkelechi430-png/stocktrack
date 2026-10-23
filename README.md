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

## Known limits / future work
Barcode scanning, sales tracking, multiple staff accounts, supplier management, Excel export and a mobile app are not included.
