import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "digital_twin.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_connection() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cpu_percent REAL,
            memory_percent REAL,
            memory_used_gb REAL,
            memory_total_gb REAL,
            disk_percent REAL,
            disk_used_gb REAL,
            disk_total_gb REAL,
            network_sent_kbps REAL,
            network_recv_kbps REAL,
            disk_read_kbps REAL,
            disk_write_kbps REAL,
            process_count INTEGER,
            health_status TEXT
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            risk_level TEXT,
            resource TEXT,
            recommendation TEXT,
            action_type TEXT,
            status TEXT,
            verification TEXT
        );
        CREATE TABLE IF NOT EXISTS system_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT,
            description TEXT
        );
        """)


def insert_metrics(metrics, health_status):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO system_metrics (
                timestamp, cpu_percent, memory_percent, memory_used_gb,
                memory_total_gb, disk_percent, disk_used_gb, disk_total_gb,
                network_sent_kbps, network_recv_kbps, disk_read_kbps,
                disk_write_kbps, process_count, health_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics["timestamp"].isoformat(), metrics["cpu_percent"],
            metrics["memory_percent"], metrics["memory_used_gb"],
            metrics["memory_total_gb"], metrics["disk_percent"],
            metrics["disk_used_gb"], metrics["disk_total_gb"],
            metrics["network_sent_kbps"], metrics["network_recv_kbps"],
            metrics["disk_read_kbps"], metrics["disk_write_kbps"],
            metrics["process_count"], health_status
        ))


def log_recommendation(risk_level, resource, recommendation, action_type, status, verification):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO recommendations
            (timestamp, risk_level, resource, recommendation, action_type, status, verification)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), risk_level, resource,
              recommendation, action_type, status, verification))


def log_event(event_type, description):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO system_events (timestamp, event_type, description)
            VALUES (?, ?, ?)
        """, (datetime.now().isoformat(), event_type, description))


def get_metrics(limit=500):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in reversed(rows)]


def get_recommendations(limit=100):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM recommendations ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_events(limit=100):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM system_events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]
