import os
import threading
from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling

from src.config import database_config


class DatabaseError(Exception):
    """Raised when a database operation fails."""


class DatabaseConnection:
    """Singleton that owns one shared MySQL connection pool.

    Each subclass (the managers) gets exactly one instance, and all of
    them share the same pool.
    """

    _instances = {}
    _pool = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with DatabaseConnection._lock:
            if cls not in DatabaseConnection._instances:
                DatabaseConnection._instances[cls] = super().__new__(cls)
        return DatabaseConnection._instances[cls]

    @staticmethod
    def _load_config():
        """Read credentials from Streamlit secrets (cloud) or .env (local)."""
        try:
            import streamlit as st
            cfg = st.secrets["mysql"]
            return {
                "host": cfg["host"],
                "port": int(cfg.get("port", 3306)),
                "user": cfg["user"],
                "password": cfg["password"],
            }
        except Exception:
            settings = database_config("mysql")
            settings.pop("database", None)
            return settings

    @classmethod
    def _get_pool(cls):
        with DatabaseConnection._lock:
            if DatabaseConnection._pool is None:
                try:
                    DatabaseConnection._pool = pooling.MySQLConnectionPool(
                        pool_name="hr_pool",
                        pool_size=5,
                        **DatabaseConnection._load_config(),
                    )
                except mysql.connector.Error as e:
                    raise DatabaseError(f"Could not create connection pool: {e}") from e
        return DatabaseConnection._pool

    @contextmanager
    def _cursor(self):
        conn = self._get_pool().get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            yield cur
            conn.commit()
        except mysql.connector.Error as e:
            conn.rollback()
            raise DatabaseError(str(e)) from e
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()  # returns the connection to the pool

    def fetch_all(self, sql, params=None):
        with self._cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

    def fetch_one(self, sql, params=None):
        with self._cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

    def execute(self, sql, params=None):
        """Run an INSERT/UPDATE/DELETE and return the last inserted id."""
        with self._cursor() as cur:
            cur.execute(sql, params or ())
            return cur.lastrowid

    def call_procedure(self, name, args=()):
        """Run a stored procedure, optionally with positional arguments."""
        with self._cursor() as cur:
            cur.callproc(name, args)
            for result in cur.stored_results():
                result.fetchall()