"""StockTrack - a simple inventory tracker for small shops (Flask + SQLite)."""
import os
import secrets
import sqlite3
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'General',
    price REAL NOT NULL DEFAULT 0,
    quantity INTEGER NOT NULL DEFAULT 0,
    low_stock_limit INTEGER NOT NULL DEFAULT 5
);
"""


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        DATABASE=os.environ.get(
            "DATABASE", os.path.join(app.root_path, "stocktrack.db")),
        OWNER_USERNAME=os.environ.get("OWNER_USERNAME", "owner"),
        OWNER_PASSWORD=os.environ.get("OWNER_PASSWORD", "stocktrack123"),
    )
    if test_config:
        app.config.update(test_config)
    app.config["OWNER_HASH"] = generate_password_hash(app.config["OWNER_PASSWORD"])

    # ---------- database helpers ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().executescript(SCHEMA)
        get_db().commit()

    # ---------- security helpers ----------
    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("logged_in"):
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        return session["csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def check_csrf():
        if request.method == "POST":
            token = session.get("csrf")
            if not token or token != request.form.get("csrf_token"):
                abort(400, "Invalid form token. Please reload the page.")

    # ---------- validation ----------
    def parse_item_form(form):
        errors = []
        name = form.get("name", "").strip()
        category = form.get("category", "").strip() or "General"
        if not name:
            errors.append("Item name is required.")
        try:
            price = float(form.get("price", "0"))
            if price < 0:
                raise ValueError
        except ValueError:
            errors.append("Price must be a number of 0 or more.")
            price = 0
        try:
            quantity = int(form.get("quantity", "0"))
            if quantity < 0:
                raise ValueError
        except ValueError:
            errors.append("Quantity must be a whole number of 0 or more.")
            quantity = 0
        try:
            limit = int(form.get("low_stock_limit", "5"))
            if limit < 0:
                raise ValueError
        except ValueError:
            errors.append("Low-stock limit must be a whole number of 0 or more.")
            limit = 5
        data = {"name": name, "category": category, "price": price,
                "quantity": quantity, "low_stock_limit": limit}
        return data, errors

    # ---------- auth routes ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user = request.form.get("username", "")
            pw = request.form.get("password", "")
            if (user == app.config["OWNER_USERNAME"]
                    and check_password_hash(app.config["OWNER_HASH"], pw)):
                session.clear()
                session["logged_in"] = True
                return redirect(url_for("index"))
            flash("Wrong username or password.", "error")
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---------- item routes ----------
    @app.route("/")
    @login_required
    def index():
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        low_only = request.args.get("low") == "1"

        sql = "SELECT * FROM items WHERE 1=1"
        params = []
        if q:
            sql += " AND name LIKE ?"
            params.append(f"%{q}%")
        if category:
            sql += " AND category = ?"
            params.append(category)
        if low_only:
            sql += " AND quantity <= low_stock_limit"
        sql += " ORDER BY name COLLATE NOCASE"

        db = get_db()
        items = db.execute(sql, params).fetchall()
        categories = [r["category"] for r in db.execute(
            "SELECT DISTINCT category FROM items ORDER BY category")]
        return render_template("items.html", items=items, categories=categories,
                               q=q, category=category, low_only=low_only)

    @app.route("/items/new", methods=["GET", "POST"])
    @login_required
    def add_item():
        item = {"name": "", "category": "", "price": "", "quantity": "",
                "low_stock_limit": 5}
        if request.method == "POST":
            item, errors = parse_item_form(request.form)
            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                db = get_db()
                db.execute(
                    "INSERT INTO items (name, category, price, quantity, "
                    "low_stock_limit) VALUES (?, ?, ?, ?, ?)",
                    (item["name"], item["category"], item["price"],
                     item["quantity"], item["low_stock_limit"]))
                db.commit()
                flash("Item added.", "success")
                return redirect(url_for("index"))
        return render_template("item_form.html", item=item, title="Add item")

    @app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_item(item_id):
        db = get_db()
        row = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            abort(404)
        item = dict(row)
        if request.method == "POST":
            item, errors = parse_item_form(request.form)
            item["id"] = item_id
            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                db.execute(
                    "UPDATE items SET name=?, category=?, price=?, quantity=?, "
                    "low_stock_limit=? WHERE id=?",
                    (item["name"], item["category"], item["price"],
                     item["quantity"], item["low_stock_limit"], item_id))
                db.commit()
                flash("Item updated.", "success")
                return redirect(url_for("index"))
        return render_template("item_form.html", item=item, title="Edit item")

    @app.route("/items/<int:item_id>/delete", methods=["POST"])
    @login_required
    def delete_item(item_id):
        db = get_db()
        db.execute("DELETE FROM items WHERE id = ?", (item_id,))
        db.commit()
        flash("Item deleted.", "success")
        return redirect(url_for("index"))

    @app.route("/summary")
    @login_required
    def summary():
        db = get_db()
        totals = db.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(quantity), 0) AS units, "
            "COALESCE(SUM(quantity * price), 0) AS value FROM items").fetchone()
        low_items = db.execute(
            "SELECT * FROM items WHERE quantity <= low_stock_limit "
            "ORDER BY quantity, name COLLATE NOCASE").fetchall()
        return render_template("summary.html", totals=totals, low_items=low_items)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
