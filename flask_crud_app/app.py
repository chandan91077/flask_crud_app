import os
import sqlite3
from pathlib import Path
from typing import Optional

from flask import Flask, current_app, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BASE_DIR / "items.db"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        db_path = current_app.config.get("DATABASE", str(DEFAULT_DB))
        os.makedirs(os.path.dirname(db_path), exist_ok=True) if os.path.dirname(db_path) else None
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        SECRET_KEY="dev-secret-key",
        DATABASE=str(DEFAULT_DB),
        PAGE_SIZE=6,
    )
    if test_config:
        app.config.update(test_config)

    app.teardown_appcontext(close_db)

    @app.before_request
    def ensure_db():
        get_db()

    @app.route("/")
    def index():
        return redirect(url_for("list_items"))

    @app.route("/items", methods=["GET"])
    def list_items():
        search = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "").strip()
        sort = request.args.get("sort", "created_at")
        direction = request.args.get("direction", "desc")
        page = max(int(request.args.get("page", 1)), 1)

        db = get_db()
        query = "SELECT * FROM items"
        clauses = []
        params = []
        if search:
            clauses.append("name LIKE ?")
            params.append(f"%{search}%")
        if category:
            clauses.append("category = ?")
            params.append(category)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        order_by = "created_at"
        if sort in {"name", "category", "status", "created_at"}:
            order_by = sort
        query += f" ORDER BY {order_by} {'DESC' if direction == 'desc' else 'ASC'}"

        rows = db.execute(query, params).fetchall()
        total = len(rows)
        page_size = app.config.get("PAGE_SIZE", 6)
        start = (page - 1) * page_size
        end = start + page_size
        items = rows[start:end]

        last_page = max((total + page_size - 1) // page_size, 1)
        return render_template(
            "index.html",
            items=items,
            page=page,
            last_page=last_page,
            search=search,
            category=category,
            status=status,
            sort=sort,
            direction=direction,
        )

    @app.route("/items/new", methods=["GET", "POST"])
    def new_item():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            status = request.form.get("status", "").strip()
            if not name or not category or not status:
                flash("All fields are required.")
                return redirect(url_for("new_item"))
            db = get_db()
            db.execute(
                "INSERT INTO items (name, category, status) VALUES (?, ?, ?)",
                (name, category, status),
            )
            db.commit()
            flash("Item created successfully.")
            return redirect(url_for("list_items"))
        return render_template("form.html", item=None, title="Create item")

    @app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
    def edit_item(item_id: int):
        db = get_db()
        item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not item:
            flash("Item not found.")
            return redirect(url_for("list_items"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            status = request.form.get("status", "").strip()
            if not name or not category or not status:
                flash("All fields are required.")
                return redirect(url_for("edit_item", item_id=item_id))
            db.execute(
                "UPDATE items SET name = ?, category = ?, status = ? WHERE id = ?",
                (name, category, status, item_id),
            )
            db.commit()
            flash("Item updated successfully.")
            return redirect(url_for("list_items"))
        return render_template("form.html", item=item, title="Edit item")

    @app.route("/items/<int:item_id>/delete", methods=["POST"])
    def delete_item(item_id: int):
        db = get_db()
        db.execute("DELETE FROM items WHERE id = ?", (item_id,))
        db.commit()
        flash("Item deleted successfully.")
        return redirect(url_for("list_items"))

    with app.app_context():
        init_db()

    return app
