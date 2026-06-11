# 🗄️ sqlite-api

> Drop a SQLite file, get an instant REST API — with **OpenAPI docs, filtering, pagination, and full CRUD**. Single command, zero config.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/fastapi-0.109+-teal.svg" alt="FastAPI">
</p>

## ✨ Features

- 🪄 **Auto-discovery** — reads your SQLite schema, creates REST endpoints for every table
- 📖 **OpenAPI/Swagger docs** — `/docs` gives you interactive API documentation
- 🔍 **Filtering** — `?column=value` filters on any column
- 📄 **Pagination** — `?limit=50&offset=0` built in
- 🔃 **Sorting** — `?sort=column&order=desc`
- ✍️ **Full CRUD** — `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
- 🔒 **Read-only mode** — `--readonly` for production-safe read access
- 🏃 **Single binary feel** — one `pip install`, one command

## 🚀 Quick Start

```bash
# Install
pip install sqlite-api

# Point at any SQLite file
sqlite-api my-database.db

# Open browser → http://localhost:8080/docs
```

## 📦 Usage

```
sqlite-api DATABASE [options]

Arguments:
  DATABASE          Path to SQLite file

Options:
  -H, --host HOST   Bind address (default: 0.0.0.0)
  -p, --port PORT   Port number (default: 8080)
  -r, --readonly    Read-only mode, disables POST/PUT/DELETE
  -t, --title TEXT  Custom API title
  -v, --version     Show version
```

## 🔧 API Reference

| Method   | Endpoint               | Description                     |
| -------- | ---------------------- | ------------------------------- |
| `GET`    | `/api/{table}`         | List rows (paginated, filtered) |
| `GET`    | `/api/{table}/{id}`    | Get single row by PK            |
| `POST`   | `/api/{table}`         | Create a new row                |
| `PUT`    | `/api/{table}/{id}`    | Full update                     |
| `PATCH`  | `/api/{table}/{id}`    | Partial update                  |
| `DELETE` | `/api/{table}/{id}`    | Delete a row                    |
| `GET`    | `/api/_query?q=SELECT` | Run raw SELECT query            |
| `GET`    | `/`                    | Database schema (JSON)          |
| `GET`    | `/docs`                | Swagger UI                      |

### Examples

```bash
# List users with pagination
curl "http://localhost:8080/api/users?limit=20&offset=0"

# Filter by name
curl "http://localhost:8080/api/users?name=Alice"

# Sort by created_at descending
curl "http://localhost:8080/api/users?sort=created_at&order=desc"

# Get user #1
curl http://localhost:8080/api/users/1

# Create a user
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@example.com"}'

# Update a user
curl -X PUT http://localhost:8080/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith"}'

# Delete a user
curl -X DELETE http://localhost:8080/api/users/1

# Raw SQL query
curl "http://localhost:8080/api/_query?q=SELECT+name,COUNT(*)+FROM+users+GROUP+BY+name"
```

## 🛡️ Security

- **Identifier sanitization** — table and column names are validated against SQL injection
- **Read-only mode** — `--readonly` disables all write operations
- **Query length limit** — raw query endpoint capped at 4000 chars
- **SELECT-only raw queries** — `/api/_query` rejects non-SELECT statements

⚠️ **Production use:** Run behind a reverse proxy (nginx/Caddy) with auth. This is a development/ admin tool — add your own auth layer for public exposure.

## 🏗️ How It Works

```
$ sqlite-api chinook.db
     │
     ▼
┌─────────────────────────────────────┐
│  FastAPI Server (auto-generated)    │
│                                     │
│  GET    /api/albums   → SELECT ...  │
│  POST   /api/albums   → INSERT ...  │
│  PUT    /api/albums/1 → UPDATE ...  │
│  DELETE /api/albums/1 → DELETE ...  │
│                                     │
│  /docs  → Swagger UI (auto)         │
│  /api/_query?q=... → Raw SQL       │
└─────────────────────────────────────┘
```

## 📄 License

MIT — use it, fork it, ship it.

---

⭐ **Star this repo** if you find it useful! PRs welcome.
