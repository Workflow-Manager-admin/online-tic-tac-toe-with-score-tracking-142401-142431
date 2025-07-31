#!/usr/bin/env python3
"""Initialize or migrate the SQLite database for the Tic Tac Toe application.

Creates the following tables with appropriate indices and foreign key constraints:
- users: id, username, password_hash, score, created_at
- games: id, player_x_id, player_o_id, winner_id, status, started_at, finished_at
- moves: id, game_id, user_id, row, col, move_num, created_at
- scores: user_id, total_games, wins, losses, draws

This script handles schema creation (if not present) and safe application of future schema updates.
"""

import sqlite3
import os
import datetime

DB_NAME = "myapp.db"
DB_PATH = os.path.abspath(DB_NAME)
SCHEMA_VERSION = 1  # Increment if/when schema changes

def get_conn():
    """Get a connection to the SQLite DB enabling foreign keys."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# PUBLIC_INTERFACE
def create_tables(conn):
    """Create tables for users, games, moves, and scores."""
    cursor = conn.cursor()

    # Create schema_migrations table to track applied migrations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Index on username
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")

    # Create games table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_x_id INTEGER NOT NULL,
            player_o_id INTEGER NOT NULL,
            winner_id INTEGER,
            status TEXT NOT NULL CHECK(status IN ('waiting', 'active', 'finished')),
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            FOREIGN KEY(player_x_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(player_o_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(winner_id) REFERENCES users(id)
        )
    """)

    # Index on status for efficient game state queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_status ON games (status)")

    # Create moves table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            row INTEGER NOT NULL CHECK(row BETWEEN 0 AND 2),
            col INTEGER NOT NULL CHECK(col BETWEEN 0 AND 2),
            move_num INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    # Composite index for moves per game
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_moves_gameid ON moves (game_id)")

    # Create scores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            user_id INTEGER PRIMARY KEY,
            total_games INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            draws INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Now mark the current schema as applied in migrations table if not already present
    cursor.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)", (SCHEMA_VERSION,))

    conn.commit()

# PUBLIC_INTERFACE
def is_schema_up_to_date(conn):
    """Check if the schema version is already applied."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(version) FROM schema_migrations")
    row = cursor.fetchone()
    return (row and row[0] == SCHEMA_VERSION)

# PUBLIC_INTERFACE
def initialize_db():
    """Create SQLite DB and tables if not already present. Migrate if schema outdated."""
    print("Checking for existing SQLite database ...")
    db_exists = os.path.exists(DB_NAME)
    conn = get_conn()

    if not db_exists:
        print(f"Database will be created at {DB_PATH}")
    else:
        print(f"Database found at {DB_PATH}")

    if not is_schema_up_to_date(conn):
        print("Applying database schema ...")
        create_tables(conn)
        print("Schema created or updated successfully.")
    else:
        print("Schema already up-to-date.")

    # Save DB connection information for external tools
    print("Writing connection info ...")
    with open("db_connection.txt", "w") as f:
        f.write(f"# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
        f.write(f"# Connection string: sqlite:///{DB_PATH}\n")
        f.write(f"# File path: {DB_PATH}\n")

    # Create .env file for Node.js visualizer
    os.makedirs("db_visualizer", exist_ok=True)
    with open("db_visualizer/sqlite.env", "w") as f:
        f.write(f'export SQLITE_DB="{DB_PATH}"\n')

    print("Database initialization complete!")
    print(f"Location: {DB_PATH}")

if __name__ == "__main__":
    print("Starting Tic Tac Toe database initialization ...")
    initialize_db()
