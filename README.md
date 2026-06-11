# 🗄️ sqlite-api

> Drop a SQLite file, get an instant REST API — with **OpenAPI docs, filtering, pagination, and full CRUD.** Single command, zero config.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/fastapi-0.109+-teal.svg" alt="FastAPI">
  <img src="https://img.shields.io/pypi/v/sqlite-api?label=pypi" alt="PyPI">
</p>

## ✨ Features

- 🪄 **Auto-discovery** — reads your SQLite schema at startup, creates REST endpoints for every table automatically
- 📖 **OpenAPI / Swagger docs** — browse `/docs` for interactive, executable API documentation
- 🔍 **Dynamic filtering** — `?column=value` filters on any column in the table
- 📄 **Pagination** — `?limit=50&offset=0` built into every list endpoint
- 🔃 **Sorting** — `?sort=column&order=desc`
- ✍️ **Full CRUD** — `GET`, `POST`, `PUT`, `PATCH`, `DELETE` on every table
- 🔒 **Read-only mode** — `--readonly` disables all write operations for production safety
- 🛡️ **SQL injection protection** — identifier sanitization on all table and column names
- 🏃 **Single-command** — `pip install sqlite-api && sqlite-api mydb.db`

## 🚀 Quick Start

```bash
# Install
pip install sqlite-api

# Point at any SQLite file
sqlite-api my-database.db

# Open your browser → http://localhost:8080/docs
```

## 📦 Usage

```
sqlite-api DATABASE [options]

Arguments:
  DATABASE          Path to the SQLite database file

Options:
  -H, --host HOST   Bind address (default: 0.0.0.0)
  -p, --port PORT   Port number (default: 8080)
  -r, --readonly    Read-only mode — disables POST/PUT/PATCH/DELETE
  -t, --title TEXT  Custom API title displayed in docs
  -v, --version     Print version number
```

## 🔧 API Reference

| Method   | Endpoint               | Description                                |
| -------- | ---------------------- | ------------------------------------------ |
| `GET`    | `/api/{table}`         | List rows — paginated, filterable, sortable |
| `GET`    | `/api/{table}/{id}`    | Get a single row by primary key            |
| `POST`   | `/api/{table}`         | Create a new row                           |
| `PUT`    | `/api/{table}/{id}`    | Full update of a row                       |
| `PATCH`  | `/api/{table}/{id}`    | Partial update of a row                    |
| `DELETE` | `/api/{table}/{id}`    | Delete a row                               |
| `GET`    | `/api/_query?q=SELECT` | Run a raw SELECT query (read-only)         |
| `GET`    | `/`                    | Database schema and endpoint listing (JSON) |
| `GET`    | `/docs`                | Interactive Swagger UI                     |
| `GET`    | `/api`                 | HTML landing page with examples            |

### Examples

```bash
# List users with pagination
curl "http://localhost:8080/api/users?limit=20&offset=0"

# Filter by name
curl "http://localhost:8080/api/users?name=Alice"

# Sort by creation date, newest first
curl "http://localhost:8080/api/users?sort=created_at&order=desc"

# Get a single user
curl http://localhost:8080/api/users/1

# Create a new user
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@example.com"}'

# Update a user
curl -X PUT http://localhost:8080/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith"}'

# Partial update
curl -X PATCH http://localhost:8080/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"email": "new-email@example.com"}'

# Delete a user
curl -X DELETE http://localhost:8080/api/users/1

# Run a raw SQL query
curl "http://localhost:8080/api/_query?q=SELECT+name,COUNT(*)+FROM+users+GROUP+BY+name"
```

## 🛡️ Security

- **Identifier sanitization** — all table and column names are validated with strict regex (`^[a-zA-Z_][a-zA-Z0-9_]*$`)
- **Read-only mode** — `--readonly` flag disables all write operations at the route level
- **Query length limit** — raw SQL queries capped at 4000 characters
- **SELECT-only** — the `/api/_query` endpoint rejects any non-SELECT statement

⚠️ **Production note:** Run behind a reverse proxy (nginx/Caddy) with authentication. This tool is designed for development, admin dashboards, and internal tooling — add your own auth layer before exposing to the public internet.

## 🏗️ How It Works

```
$ sqlite-api chinook.db
     │
     ▼
┌─────────────────────────────────────────────┐
│  FastAPI Server  (routes auto-generated)     │
│                                              │
│  GET    /api/albums    → SELECT * FROM ...   │
│  POST   /api/albums    → INSERT INTO ...     │
│  PUT    /api/albums/1  → UPDATE ... SET ...  │
│  DELETE /api/albums/1  → DELETE FROM ...     │
│                                              │
│  /docs      → Swagger UI  (auto-generated)   │
│  /api/_query?q=... → Raw SELECT (read-only) │
│  /          → DB schema listing (JSON)       │
└─────────────────────────────────────────────┘
```

## 🔧 Development

```bash
git clone https://github.com/test-qtj/sqlite-api
cd sqlite-api
pip install -e .
```

## 🤝 Contributing

Ideas welcome:
- Authentication middleware integration
- WebSocket support for live updates
- Multiple database support (attach multiple SQLite files)
- Query builder UI at `/api`

## 📄 License

MIT © 2024 — use it, fork it, ship it.

---

⭐ **Star this repo** if you've ever wanted a REST API from a SQLite file in one command!
