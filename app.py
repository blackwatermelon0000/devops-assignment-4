import os
import time
from contextlib import closing

from flask import Flask, redirect, render_template, request, url_for
import mysql.connector
from mysql.connector import Error

APP_NAME = "Notes App"

DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "notesdb")

app = Flask(__name__)


def get_connection(database=None):
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database,
    )


def init_db():
    # Wait for MySQL to be ready when containers start.
    for _ in range(30):
        try:
            with closing(get_connection()) as conn:
                conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
                conn.commit()
            break
        except Error:
            time.sleep(2)

    with closing(get_connection(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


@app.route("/", methods=["GET", "POST"])
def index():
    init_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if title and content:
            with closing(get_connection(DB_NAME)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO notes (title, content) VALUES (%s, %s)",
                    (title, content),
                )
                conn.commit()
        return redirect(url_for("index"))

    with closing(get_connection(DB_NAME)) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, content, created_at FROM notes ORDER BY id DESC")
        notes = cursor.fetchall()

    return render_template("index.html", app_name=APP_NAME, notes=notes)


@app.route("/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    init_db()
    with closing(get_connection(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
        conn.commit()
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
