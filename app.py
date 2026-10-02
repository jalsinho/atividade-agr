import os
import sqlite3
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "mural-local-dev-key")
app.config["DATABASE"] = Path(app.instance_path) / "mural.sqlite3"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_db():
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    database = get_db()
    database.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            contact TEXT NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('perdido', 'encontrado')),
            status TEXT NOT NULL CHECK (status IN ('Aberto', 'Encontrado', 'Devolvido')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    database.commit()


@app.before_request
def ensure_database():
    init_db()


@app.get("/")
def index():
    kind_filter = request.args.get("tipo", "todos")
    status_filter = request.args.get("status", "todos")
    search = request.args.get("q", "").strip()

    conditions = []
    values = []
    if kind_filter in ("perdido", "encontrado"):
        conditions.append("kind = ?")
        values.append(kind_filter)
    if status_filter in ("Aberto", "Encontrado", "Devolvido"):
        conditions.append("status = ?")
        values.append(status_filter)
    if search:
        conditions.append("(name LIKE ? OR description LIKE ? OR location LIKE ?)")
        values.extend([f"%{search}%"] * 3)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    items = get_db().execute(
        f"SELECT * FROM items {where} ORDER BY created_at DESC, id DESC", values
    ).fetchall()
    totals = get_db().execute(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN status != 'Devolvido' THEN 1 ELSE 0 END) AS active "
        "FROM items"
    ).fetchone()

    return render_template(
        "index.html",
        items=items,
        total=totals["total"],
        active=totals["active"] or 0,
        kind_filter=kind_filter,
        status_filter=status_filter,
        search=search,
    )


@app.post("/itens")
def create_item():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    location = request.form.get("location", "").strip()
    contact = request.form.get("contact", "").strip()
    kind = request.form.get("kind", "")

    if not all((name, description, location, contact)) or kind not in ("perdido", "encontrado"):
        flash("Preencha todos os campos para publicar o item.", "error")
        return redirect(url_for("index"))

    status = "Aberto" if kind == "perdido" else "Encontrado"
    database = get_db()
    database.execute(
        "INSERT INTO items (name, description, location, contact, kind, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, description, location, contact, kind, status),
    )
    database.commit()
    flash("Item publicado no mural.", "success")
    return redirect(url_for("index"))


@app.post("/itens/<int:item_id>/status")
def update_status(item_id):
    database = get_db()
    item = database.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item is None:
        abort(404)

    next_status = {
        ("perdido", "Aberto"): "Encontrado",
        ("perdido", "Encontrado"): "Devolvido",
        ("encontrado", "Encontrado"): "Devolvido",
    }.get((item["kind"], item["status"]))
    if next_status is None:
        flash("Este item já foi devolvido.", "error")
    else:
        database.execute("UPDATE items SET status = ? WHERE id = ?", (next_status, item_id))
        database.commit()
        flash(f"Status atualizado: {next_status.lower()}.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)