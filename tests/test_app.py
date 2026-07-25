import os
import tempfile

import pytest

from flask_crud_app.app import create_app, init_db


@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(db_fd)

    app = create_app({"TESTING": True, "DATABASE": db_path})
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

    os.unlink(db_path)


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
    assert "Item 0" in html
    assert "Item 5" in html
    assert "Item 11" not in html


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
