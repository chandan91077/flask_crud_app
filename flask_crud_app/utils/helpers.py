from flask import request

ALLOWED_SORT_FIELDS = {"name", "category", "status", "created_at"}


def get_page() -> int:
    page = request.args.get("page", default=1, type=int) or 1
    return max(page, 1)


def paginate_rows(rows: list[dict], page: int, page_size: int) -> list[dict]:
    start = (page - 1) * page_size
    return rows[start : start + page_size]


def build_item_query() -> tuple[str, list[str]]:
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "created_at")
    direction = request.args.get("direction", "desc")

    clauses = []
    params: list[str] = []

    if search:
        clauses.append("name LIKE %s")
        params.append(f"%{search}%")
    if category:
        clauses.append("category = %s")
        params.append(category)
    if status:
        clauses.append("status = %s")
        params.append(status)

    query = "SELECT * FROM items"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    order_by = sort if sort in ALLOWED_SORT_FIELDS else "created_at"
    order_direction = "DESC" if direction == "desc" else "ASC"
    query += f" ORDER BY {order_by} {order_direction}, id {order_direction}"
    return query, params
