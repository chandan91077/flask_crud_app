import os
from typing import Optional

import pymysql
import pymysql.cursors
from flask import current_app, g


def get_db():
    if "db" not in g:
        host = current_app.config.get("MYSQL_HOST") or os.environ.get("MYSQL_HOST", "localhost")
        port = int(current_app.config.get("MYSQL_PORT") or os.environ.get("MYSQL_PORT", 3306))
        user = current_app.config.get("MYSQL_USER") or os.environ.get("MYSQL_USER", "root")
        password = current_app.config.get("MYSQL_PASSWORD") or os.environ.get("MYSQL_PASSWORD", "7410")
        database = current_app.config.get("MYSQL_DB") or os.environ.get("MYSQL_DB", "flask_crud")

        g.db = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def init_db():
    host = current_app.config.get("MYSQL_HOST") or os.environ.get("MYSQL_HOST", "localhost")
    port = int(current_app.config.get("MYSQL_PORT") or os.environ.get("MYSQL_PORT", 3306))
    user = current_app.config.get("MYSQL_USER") or os.environ.get("MYSQL_USER", "root")
    password = current_app.config.get("MYSQL_PASSWORD") or os.environ.get("MYSQL_PASSWORD", "7410")
    database = current_app.config.get("MYSQL_DB") or os.environ.get("MYSQL_DB", "flask_crud")

    try:
        # Connect to MySQL server to ensure database exists
        server_conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            autocommit=True,
        )
        with server_conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
        server_conn.close()

        # Connect to the target database and ensure table exists
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
    except Exception as err:
        print(f"[MySQL Init Warning] Could not connect to MySQL server: {err}")
