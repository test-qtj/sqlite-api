"""Dynamic REST API server for SQLite databases."""

import sqlite3
import re
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


def _is_safe_identifier(name: str) -> bool:
    """Only allow alphanumeric + underscore identifiers."""
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))


def _safe_column(name: str) -> str:
    """Quote a column name for SQLite."""
    if not _is_safe_identifier(name):
        raise HTTPException(400, f"Invalid column name: {name}")
    return f'"{name}"'


def _safe_table(name: str) -> str:
    """Quote a table name for SQLite."""
    if not _is_safe_identifier(name):
        raise HTTPException(400, f"Invalid table name: {name}")
    return f'"{name}"'


def _serialize_value(v: Any) -> Any:
    """Convert Python values to JSON-safe types."""
    if isinstance(v, bytes):
        return "[BLOB]"
    if isinstance(v, (int, float, str, type(None))):
        return v
    return str(v)


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def build_app(db_path: str, read_only: bool = False, title: str = "SQLite API") -> FastAPI:
    """Build a FastAPI app with dynamic routes for all tables in the SQLite database."""

    app = FastAPI(
        title=title,
        description=f"Auto-generated REST API for `{db_path}`",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def discover_tables() -> list[dict]:
        conn = _get_conn(db_path)
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            result = []
            for (table_name,) in tables:
                cols = conn.execute(f"PRAGMA table_info({_safe_table(table_name)})").fetchall()
                columns = [
                    {
                        "name": c[1], "type": c[2],
                        "notnull": bool(c[3]), "pk": bool(c[5]),
                    }
                    for c in cols
                ]
                row_count = conn.execute(
                    f"SELECT COUNT(*) FROM {_safe_table(table_name)}"
                ).fetchone()[0]
                result.append({"name": table_name, "columns": columns, "row_count": row_count})
            return result
        finally:
            conn.close()

    # ── Root / Schema endpoint ──
    @app.get("/")
    def api_root(request: Request):
        tables = discover_tables()
        base = str(request.base_url).rstrip("/")
        return {
            "database": db_path,
            "title": title,
            "tables": len(tables),
            "endpoints": {
                "docs": f"{base}/docs",
                "openapi": f"{base}/openapi.json",
            },
            "tables_detail": [
                {
                    "name": t["name"],
                    "columns": [c["name"] for c in t["columns"]],
                    "row_count": t["row_count"],
                    "endpoints": {
                        "list": f"{base}/api/{t['name']}",
                        "get": f"{base}/api/{t['name']}/{{id}}",
                    },
                }
                for t in tables
            ],
        }

    # ── Build dynamic routes per table ──
    routes = _build_table_routes(db_path, read_only)
    for path, methods in routes.items():
        for method, handler in methods.items():
            app.add_api_route(path, handler, methods=[method])

    # ── Ad-hoc SQL endpoint ──
    @app.get("/api/_query")
    def run_query(q: str = Query(..., min_length=1, max_length=4000)):
        if not q.strip().upper().startswith("SELECT"):
            raise HTTPException(400, "Only SELECT queries allowed via this endpoint")
        conn = _get_conn(db_path)
        try:
            rows = conn.execute(q).fetchall()
            if rows:
                cols = list(rows[0].keys())
                return {
                    "columns": cols, "count": len(rows),
                    "rows": [{c: _serialize_value(r[c]) for c in cols} for r in rows],
                }
            return {"columns": [], "count": 0, "rows": []}
        except sqlite3.Error as e:
            raise HTTPException(400, str(e))
        finally:
            conn.close()

    # ── HTML landing page ──
    @app.get("/api", response_class=HTMLResponse)
    def api_landing():
        tables_info = discover_tables()
        table_rows = ""
        for t in tables_info:
            cols = ", ".join(c["name"] for c in t["columns"][:5])
            if len(t["columns"]) > 5:
                cols += "..."
            table_rows += f"""
            <tr>
                <td><a href="/api/{t['name']}"><code>/api/{t['name']}</code></a></td>
                <td>{t['row_count']}</td>
                <td>{cols}</td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1.5rem; background: #111; color: #eee; }}
  h1 {{ font-size: 2rem; }}
  a {{ color: #818cf8; }}
  code {{ background: #1e293b; padding: .15em .4em; border-radius: 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; }}
  th, td {{ padding: .6em .8em; border-bottom: 1px solid #333; text-align: left; }}
  th {{ background: #1e293b; color: #94a3b8; font-size: .85rem; text-transform: uppercase; }}
  .badge {{ display: inline-block; padding: .2em .5em; border-radius: 999px; font-size: .75rem; }}
  .badge-get {{ background: #166534; color: #4ade80; }}
  .badge-post {{ background: #1e3a5f; color: #60a5fa; }}
  .badge-put {{ background: #713f12; color: #fbbf24; }}
  .badge-delete {{ background: #7f1d1d; color: #f87171; }}
  pre {{ background: #1e293b; padding: 1em; border-radius: 8px; overflow-x: auto; }}
  .section {{ margin: 2rem 0; }}
</style>
</head>
<body>
<h1>🗄️ {title}</h1>
<p>Database: <span style="color:#60a5fa;font-family:monospace;">{db_path}</span></p>
<p>
  <a href="/docs">📖 OpenAPI Docs (Swagger)</a> &nbsp;|&nbsp;
  <a href="/openapi.json">📄 OpenAPI JSON</a> &nbsp;|&nbsp;
  <a href="/">🏠 API Root (JSON)</a>
</p>
<div class="section">
<h2>📋 Tables ({len(tables_info)})</h2>
<table>
  <tr><th>Endpoint</th><th>Rows</th><th>Columns</th></tr>
  {table_rows}
</table>
</div>
<div class="section">
<h2>🔧 Quick Examples</h2>
<pre><code># List all rows (with pagination)
curl http://localhost:8080/api/users?limit=10&offset=0

# Filter by column value
curl "http://localhost:8080/api/users?name=Alice"

# Get single row by primary key
curl http://localhost:8080/api/users/1

# Sort results
curl "http://localhost:8080/api/users?sort=name&order=asc"

# Create a row
curl -X POST http://localhost:8080/api/users \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "Bob", "email": "bob@example.com"}}'

# Update a row
curl -X PUT http://localhost:8080/api/users/1 \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "Alice Updated"}}'

# Delete a row
curl -X DELETE http://localhost:8080/api/users/1

# Run a raw SELECT query
curl "http://localhost:8080/api/_query?q=SELECT+*+FROM+users+ORDER+BY+name"</code></pre>
</div>
</body>
</html>"""

    return app


def _build_table_routes(db_path: str, read_only: bool) -> dict:
    """Build route handlers for all tables. Returns {path: {method: handler}}."""

    conn = _get_conn(db_path)
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    finally:
        conn.close()

    routes = {}

    for (table_name,) in tables:
        # Get column info
        conn = _get_conn(db_path)
        try:
            cols = conn.execute(f"PRAGMA table_info({_safe_table(table_name)})").fetchall()
            col_names = [c[1] for c in cols]
            pk_cols = [c[1] for c in cols if c[5]]
            pk_col = pk_cols[0] if pk_cols else (col_names[0] if col_names else "rowid")
        finally:
            conn.close()

        # Factory to create handlers with proper closure capture
        def _make_list_handler(tn, cn, pc):
            async def handler(request: Request,
                              limit: int = Query(50, ge=1, le=10000),
                              offset: int = Query(0, ge=0),
                              sort: str = Query(""),
                              order: str = Query("asc")):
                reserved = {"limit", "offset", "sort", "order"}
                filters = []
                filter_values = []
                for key, values in request.query_params.multi_items():
                    if key in reserved:
                        continue
                    if key in cn and _is_safe_identifier(key):
                        filters.append(f'"{key}" = ?')
                        filter_values.append(values)

                where = f"WHERE {' AND '.join(filters)}" if filters else ""
                order_clause = ""
                if sort and sort in cn and _is_safe_identifier(sort):
                    direction = "DESC" if order.lower() == "desc" else "ASC"
                    order_clause = f'ORDER BY "{sort}" {direction}'

                conn = _get_conn(db_path)
                try:
                    count_sql = f"SELECT COUNT(*) FROM {_safe_table(tn)} {where}"
                    total = conn.execute(count_sql, filter_values).fetchone()[0]
                    sql = f"SELECT * FROM {_safe_table(tn)} {where} {order_clause} LIMIT ? OFFSET ?"
                    rows = conn.execute(sql, filter_values + [limit, offset]).fetchall()
                    results = [{c: _serialize_value(row[c]) for c in cn} for row in rows]
                    return {"table": tn, "total": total, "limit": limit,
                            "offset": offset, "count": len(results), "rows": results}
                finally:
                    conn.close()
            return handler

        def _make_get_handler(tn, cn, pc):
            async def handler(row_id: str):
                conn = _get_conn(db_path)
                try:
                    sql = f"SELECT * FROM {_safe_table(tn)} WHERE {_safe_column(pc)} = ?"
                    row = conn.execute(sql, [row_id]).fetchone()
                    if row is None:
                        raise HTTPException(404, f"Row not found: {pc}={row_id}")
                    return {c: _serialize_value(row[c]) for c in cn}
                finally:
                    conn.close()
            return handler

        def _make_create_handler(tn, cn, pks):
            async def handler(request: Request):
                body = await request.json()
                if not body:
                    raise HTTPException(400, "Request body required")
                auto_pk = pks[0] if len(pks) == 1 else None
                insert_data = {}
                for k, v in body.items():
                    if k in cn and k != auto_pk and _is_safe_identifier(k):
                        insert_data[k] = v
                if not insert_data:
                    raise HTTPException(400, "No valid columns in request body")
                cols_str = ", ".join(f'"{c}"' for c in insert_data)
                placeholders = ", ".join("?" for _ in insert_data)
                values = list(insert_data.values())
                conn = _get_conn(db_path)
                try:
                    cursor = conn.execute(
                        f"INSERT INTO {_safe_table(tn)} ({cols_str}) VALUES ({placeholders})", values)
                    conn.commit()
                    new_id = cursor.lastrowid
                    if auto_pk:
                        row = conn.execute(
                            f"SELECT * FROM {_safe_table(tn)} WHERE {_safe_column(auto_pk)} = ?",
                            [new_id]).fetchone()
                    else:
                        row = conn.execute(
                            f"SELECT * FROM {_safe_table(tn)} WHERE rowid = ?", [new_id]).fetchone()
                    return {c: _serialize_value(row[c]) for c in cn} if row else {}
                except sqlite3.IntegrityError as e:
                    raise HTTPException(409, str(e))
                finally:
                    conn.close()
            return handler

        def _make_update_handler(tn, cn, pc):
            async def handler(row_id: str, request: Request):
                body = await request.json()
                if not body:
                    raise HTTPException(400, "Request body required")
                update_data = {}
                for k, v in body.items():
                    if k in cn and k != pc and _is_safe_identifier(k):
                        update_data[k] = v
                if not update_data:
                    raise HTTPException(400, "No valid columns to update")
                sets = ", ".join(f'"{c}" = ?' for c in update_data)
                values = list(update_data.values()) + [row_id]
                conn = _get_conn(db_path)
                try:
                    cursor = conn.execute(
                        f"UPDATE {_safe_table(tn)} SET {sets} WHERE {_safe_column(pc)} = ?", values)
                    conn.commit()
                    if cursor.rowcount == 0:
                        raise HTTPException(404, f"Row not found: {pc}={row_id}")
                    row = conn.execute(
                        f"SELECT * FROM {_safe_table(tn)} WHERE {_safe_column(pc)} = ?",
                        [row_id]).fetchone()
                    return {c: _serialize_value(row[c]) for c in cn} if row else {}
                finally:
                    conn.close()
            return handler

        def _make_delete_handler(tn, pc):
            async def handler(row_id: str):
                conn = _get_conn(db_path)
                try:
                    cursor = conn.execute(
                        f"DELETE FROM {_safe_table(tn)} WHERE {_safe_column(pc)} = ?", [row_id])
                    conn.commit()
                    if cursor.rowcount == 0:
                        raise HTTPException(404, f"Row not found: {pc}={row_id}")
                    return {"deleted": True, pc: row_id}
                finally:
                    conn.close()
            return handler

        routes.setdefault(f"/api/{table_name}", {})["GET"] = _make_list_handler(
            table_name, col_names, pk_col)
        routes.setdefault(f"/api/{table_name}/{{row_id}}", {})["GET"] = _make_get_handler(
            table_name, col_names, pk_col)

        if not read_only:
            routes.setdefault(f"/api/{table_name}", {})["POST"] = _make_create_handler(
                table_name, col_names, pk_cols)
            routes.setdefault(f"/api/{table_name}/{{row_id}}", {})["PUT"] = _make_update_handler(
                table_name, col_names, pk_col)
            routes.setdefault(f"/api/{table_name}/{{row_id}}", {})["PATCH"] = _make_update_handler(
                table_name, col_names, pk_col)
            routes.setdefault(f"/api/{table_name}/{{row_id}}", {})["DELETE"] = _make_delete_handler(
                table_name, pk_col)

    return routes
