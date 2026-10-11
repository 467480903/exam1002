from pathlib import Path
import hashlib
import hmac
import os
import sqlite3

from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "users.db"

app = Flask(__name__)


def password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", password_hash("password123")),
        )


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    if not username or not password:
        return jsonify({"message": "请输入用户名和密码"}), 400

    with get_db() as connection:
        user = connection.execute(
            "SELECT username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if user is None or not hmac.compare_digest(
        user["password_hash"], password_hash(password)
    ):
        return jsonify({"message": "用户名或密码错误"}), 401

    return jsonify({"message": "登录成功", "username": user["username"]})


if __name__ == "__main__":
    init_db()
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
