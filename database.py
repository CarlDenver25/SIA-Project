"""
database.py - shared SQLite setup + user authentication (login / register).
Passwords are never stored in plain text: PBKDF2-HMAC-SHA256 with a random salt (hashlib).
"""

import hashlib
import hmac
import os
import sqlite3

DB_FILE = "mini_project.db"
ITERATIONS = 200_000


def get_conn():
    return sqlite3.connect(DB_FILE)


def init_db():
    with get_conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   salt BLOB NOT NULL,
                   password_hash BLOB NOT NULL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS short_urls (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   original TEXT NOT NULL,
                   code TEXT UNIQUE NOT NULL,
                   clicks INTEGER DEFAULT 0,
                   created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS message_log (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   kind TEXT NOT NULL,
                   recipient TEXT NOT NULL,
                   subject TEXT,
                   body TEXT,
                   status TEXT,
                   sent_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS fake_records (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   full_name TEXT, gender TEXT, birthdate TEXT, age INTEGER,
                   address TEXT, mobile_number TEXT, email TEXT,
                   occupation TEXT, company TEXT, civil_status TEXT)"""
        )


def hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)


def register_user(username, password):
    salt = os.urandom(16)
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
                (username, salt, hash_password(password, salt)),
            )
        return True, "Account created. You can now log in."
    except sqlite3.IntegrityError:
        return False, "Username already exists."


def verify_login(username, password):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, salt, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        return None
    user_id, salt, stored = row
    return user_id if hmac.compare_digest(hash_password(password, salt), stored) else None
