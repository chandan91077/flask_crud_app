import os
from typing import Optional
from flask import Flask

from flask_crud_app.models.db import close_db, get_db, init_db
from flask_crud_app.routes.items import items_bp


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        SECRET_KEY="dev-secret-key",
        MYSQL_HOST=os.environ.get("MYSQL_HOST", "localhost"),
        MYSQL_PORT=int(os.environ.get("MYSQL_PORT", 3306)),
        MYSQL_USER=os.environ.get("MYSQL_USER", "root"),
        MYSQL_PASSWORD=os.environ.get("MYSQL_PASSWORD", "7410"),
        MYSQL_DB=os.environ.get("MYSQL_DB", "flask_crud"),
        PAGE_SIZE=6,
    )
    if test_config:
        app.config.update(test_config)

    app.teardown_appcontext(close_db)

    @app.before_request
    def ensure_db():
        get_db()

    app.register_blueprint(items_bp)

    # Legacy endpoint aliases for template compatibility
    app.add_url_rule("/", endpoint="index", view_func=app.view_functions["items.index"])
    app.add_url_rule("/items", endpoint="list_items", view_func=app.view_functions["items.list_items"], methods=["GET"])
    app.add_url_rule("/items/new", endpoint="new_item", view_func=app.view_functions["items.new_item"], methods=["GET", "POST"])
    app.add_url_rule("/items/<int:item_id>/edit", endpoint="edit_item", view_func=app.view_functions["items.edit_item"], methods=["GET", "POST"])
    app.add_url_rule("/items/<int:item_id>/delete", endpoint="delete_item", view_func=app.view_functions["items.delete_item"], methods=["POST"])

    with app.app_context():
        init_db()

    return app


__all__ = ["create_app", "get_db", "close_db", "init_db"]
