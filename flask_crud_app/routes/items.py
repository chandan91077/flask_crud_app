from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_crud_app.models.db import get_db
from flask_crud_app.utils.helpers import build_item_query, get_page, paginate_rows

items_bp = Blueprint("items", __name__)


@items_bp.route("/", endpoint="index")
def index():
    return redirect(url_for("items.list_items"))


@items_bp.route("/items", methods=["GET"], endpoint="list_items")
def list_items():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "created_at")
    direction = request.args.get("direction", "desc")
    page = get_page()

    db = get_db()
    query, params = build_item_query()
    with db.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    total = len(rows)
    page_size = current_app.config.get("PAGE_SIZE", 6)
    items = paginate_rows(rows, page, page_size)

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


@items_bp.route("/items/new", methods=["GET", "POST"], endpoint="new_item")
def new_item():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        status = request.form.get("status", "").strip()
        if not name or not category or not status:
            flash("All fields are required.")
            return redirect(url_for("items.new_item"))
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO items (name, category, status) VALUES (%s, %s, %s)",
                (name, category, status),
            )
        flash("Item created successfully.")
        return redirect(url_for("items.list_items"))
    return render_template("form.html", item=None, title="Create item")


@items_bp.route("/items/<int:item_id>/edit", methods=["GET", "POST"], endpoint="edit_item")
def edit_item(item_id: int):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()

    if not item:
        flash("Item not found.")
        return redirect(url_for("items.list_items"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        status = request.form.get("status", "").strip()
        if not name or not category or not status:
            flash("All fields are required.")
            return redirect(url_for("items.edit_item", item_id=item_id))
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE items SET name = %s, category = %s, status = %s WHERE id = %s",
                (name, category, status, item_id),
            )
        flash("Item updated successfully.")
        return redirect(url_for("items.list_items"))
    return render_template("form.html", item=item, title="Edit item")


@items_bp.route("/items/<int:item_id>/delete", methods=["POST"], endpoint="delete_item")
def delete_item(item_id: int):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
    flash("Item deleted successfully.")
    return redirect(url_for("items.list_items"))
