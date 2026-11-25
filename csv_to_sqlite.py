import csv
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(BASE_DIR, "users.csv")
DB_NAME = os.path.join(BASE_DIR, "users.db")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_row(row):
    return {
        (key or "").strip().lower().replace(" ", "_"): (value or "").strip()
        for key, value in row.items()
    }


def read_users(csv_path):
    users, skipped = [], []
    with open(csv_path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for line_number, raw_row in enumerate(reader, start=2):  
            row = normalize_row(raw_row)
            name = row.get("name") or f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            email = row.get("email", "").lower()

            if not name:
                skipped.append((line_number, "missing name"))
            elif not EMAIL_PATTERN.match(email):
                skipped.append((line_number, f"invalid email '{email}'"))
            else:
                users.append((name, email))
    return users, skipped


def init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.commit()


def insert_users(conn, users):
    before = conn.total_changes
    conn.executemany("INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)", users)
    conn.commit()
    return conn.total_changes - before


def display_users(conn):
    rows = conn.execute("SELECT id, name, email FROM users ORDER BY id").fetchall()
    if not rows:
        print("No users in the database.")
        return

    print(f"\n{'ID':<5} {'Name':<28} {'Email':<40}")
    print("-" * 75)
    for user_id, name, email in rows:
        name = name if len(name) <= 26 else name[:25] + "..."
        email = email if len(email) <= 38 else email[:37] + "..."
        print(f"{user_id:<5} {name:<28} {email:<40}")
    print(f"\nTotal users in database: {len(rows)}")


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV

    if not os.path.isfile(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        return

    try:
        users, skipped = read_users(csv_path)
    except (OSError, csv.Error, UnicodeDecodeError) as err:
        print(f"Error: could not read the CSV file ({err})")
        return

    print(f"Read {len(users)} valid rows from {csv_path}")
    for line_number, reason in skipped:
        print(f"  Skipped line {line_number}: {reason}")

    with sqlite3.connect(DB_NAME) as conn:
        init_db(conn)
        added = insert_users(conn, users)
        duplicates = len(users) - added
        print(f"Inserted {added} new users into: {DB_NAME}")
        if duplicates:
            print(f"Ignored {duplicates} duplicate email(s) already in the database.")
        display_users(conn)


if __name__ == "__main__":
    main()