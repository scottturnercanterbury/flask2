import sqlite3
from flask import g, current_app, abort

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        salary_gbp_pence INTEGER NOT NULL
    )
    """)
    db.commit()

def get_all_employees():
    return get_db().execute("SELECT * FROM employees").fetchall()

def get_employee(emp_id):
    emp = get_db().execute("SELECT * FROM employees WHERE id=?", (emp_id,)).fetchone()
    if not emp:
        abort(404)
    return emp

def create_employee(name, salary):
    db = get_db()
    db.execute("INSERT INTO employees (name, salary_gbp_pence) VALUES (?,?)", (name, salary))
    db.commit()

def update_employee(emp_id, name, salary):
    db = get_db()
    cur = db.execute("UPDATE employees SET name=?, salary_gbp_pence=? WHERE id=?", (name, salary, emp_id))
    db.commit()
    if cur.rowcount == 0:
        abort(404)

def delete_employee(emp_id):
    db = get_db()
    cur = db.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    db.commit()
    if cur.rowcount == 0:
        abort(404)
