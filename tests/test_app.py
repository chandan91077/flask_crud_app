import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from flask_crud_app import create_app


class MockPyMySQLCursor:
    def __init__(self, sqlite_conn: sqlite3.Connection):
        self.sqlite_conn = sqlite_conn
        self.last_result = []
        self.lastrowid = 0

    def execute(self, query: str, params: tuple = ()):
        if "CREATE DATABASE" in query.upper():
            return 0
        # Convert MySQL placeholders (%s) and DDL syntax to SQLite
        sqlite_query = query.replace("%s", "?")
        sqlite_query = sqlite_query.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sqlite_query = sqlite_query.replace("`", "")

        cursor = self.sqlite_conn.cursor()
        cursor.execute(sqlite_query, params)
        self.sqlite_conn.commit()

        if cursor.description:
            columns = [col[0] for col in cursor.description]
            self.last_result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            self.last_result = []

        self.lastrowid = cursor.lastrowid
        return len(self.last_result)

    def fetchall(self):
        return self.last_result

    def fetchone(self):
        return self.last_result[0] if self.last_result else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MockPyMySQLConnection:
    def __init__(self):
        self.sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)

    def cursor(self, cursorclass=None):
        return MockPyMySQLCursor(self.sqlite_conn)

    def close(self):
        pass


@pytest.fixture()
def client():
    mock_conn = MockPyMySQLConnection()
    with patch("pymysql.connect", return_value=mock_conn):
        app = create_app({"TESTING": True})
        with app.test_client() as client:
            yield client


def test_index_lists_items_and_supports_pagination(client):
    for i in range(12):
        client.post(
            "/items/new",
            data={
                "name": f"Item {i}",
                "category": "Books" if i % 2 == 0 else "Games",
                "status": "Pending" if i % 3 == 0 else "Done",
            },
            follow_redirects=True,
        )

    response = client.get("/items?page=1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Item 11" in html
    assert "Item 6" in html
    assert "Item 0" not in html


def test_search_sort_and_filter_work(client):
    client.post(
        "/items/new",
        data={"name": "Alpha", "category": "Books", "status": "Pending"},
        follow_redirects=True,
    )
    client.post(
        "/items/new",
        data={"name": "Beta", "category": "Games", "status": "Done"},
        follow_redirects=True,
    )

    response = client.get(
        "/items?search=alpha&sort=name&direction=asc&category=Books&status=Pending"
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Alpha" in html
    assert "Beta" not in html


def test_crud_lifecycle(client):
    create_response = client.post(
        "/items/new",
        data={"name": "Sample", "category": "Books", "status": "Pending"},
        follow_redirects=True,
    )
    assert create_response.status_code == 200

    response = client.get("/items")
    html = response.get_data(as_text=True)
    assert "Sample" in html

    item_id = 1
    update_response = client.post(
        f"/items/{item_id}/edit",
        data={"name": "Updated", "category": "Games", "status": "Done"},
        follow_redirects=True,
    )
    assert update_response.status_code == 200
    assert b"Updated" in update_response.data

    delete_response = client.post(f"/items/{item_id}/delete", follow_redirects=True)
    assert delete_response.status_code == 200
    assert b"Updated" not in delete_response.data
