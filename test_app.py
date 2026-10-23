import re

import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "OWNER_USERNAME": "owner",
        "OWNER_PASSWORD": "secret",
    })
    return app.test_client()


def token(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def login(client):
    t = token(client)
    return client.post("/login", data={"username": "owner", "password": "secret",
                                       "csrf_token": t}, follow_redirects=True)


def add(client, name="Rice", category="Food", price="2.5", qty="10", limit="5"):
    t = token(client, "/items/new")
    return client.post("/items/new", data={
        "name": name, "category": category, "price": price,
        "quantity": qty, "low_stock_limit": limit, "csrf_token": t},
        follow_redirects=True)


def test_login_required(client):
    r = client.get("/")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_wrong_password(client):
    t = token(client)
    r = client.post("/login", data={"username": "owner", "password": "bad",
                                    "csrf_token": t})
    assert b"Wrong username or password" in r.data


def test_login_ok(client):
    r = login(client)
    assert b"Inventory" in r.data


def test_post_without_csrf_rejected(client):
    r = client.post("/login", data={"username": "owner", "password": "secret"})
    assert r.status_code == 400


def test_add_item(client):
    login(client)
    r = add(client)
    assert b"Item added" in r.data and b"Rice" in r.data


def test_add_invalid(client):
    login(client)
    r = add(client, name="", price="-1")
    assert b"Item name is required" in r.data
    assert b"Price must be" in r.data


def test_edit_item(client):
    login(client)
    add(client)
    t = token(client, "/items/1/edit")
    r = client.post("/items/1/edit", data={
        "name": "Brown Rice", "category": "Food", "price": "3",
        "quantity": "8", "low_stock_limit": "5", "csrf_token": t},
        follow_redirects=True)
    assert b"Item updated" in r.data and b"Brown Rice" in r.data


def test_delete_item(client):
    login(client)
    add(client)
    t = token(client)
    r = client.post("/items/1/delete", data={"csrf_token": t}, follow_redirects=True)
    assert b"Item deleted" in r.data and b"Rice" not in r.data.split(b"<main>")[1]


def test_search_and_filter(client):
    login(client)
    add(client, name="Rice", category="Food")
    add(client, name="Soap", category="Home")
    r = client.get("/?q=soap")
    assert b"Soap" in r.data and b"Rice" not in r.data.split(b"<tbody>")[1]
    r = client.get("/?category=Food")
    assert b"Rice" in r.data and b"Soap" not in r.data.split(b"<tbody>")[1]


def test_low_stock_alert_and_summary(client):
    login(client)
    add(client, name="Rice", qty="10", limit="5")
    add(client, name="Sugar", qty="2", limit="5")
    r = client.get("/")
    assert b"LOW" in r.data
    r = client.get("/?low=1")
    body = r.data.split(b"<tbody>")[1]
    assert b"Sugar" in body and b"Rice" not in body
    r = client.get("/summary")
    assert b"Total items" in r.data and b"Sugar" in r.data
