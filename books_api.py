import os
import sqlite3
import requests

API_URL = "https://www.googleapis.com/books/v1/volumes"
API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY")  
MAX_RESULTS = 40  
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "books.db")

def fetch_books(query, limit):
    """Fetch books from the API. Returns a list of (title, author, year) tuples."""
    params = {
        "q": query,
        "maxResults": min(limit, MAX_RESULTS),
        "printType": "books",
        "key": API_KEY,
    }
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as err:
        status = err.response.status_code if err.response is not None else None
        if status == 400:
            print("Error: bad request. Check that your API key is valid.")
        elif status == 403:
            print("Error: access denied. Make sure the Books API is enabled for your key.")
        elif status == 429:
            print("Error: rate limit reached. Wait a bit and try again.")
        else:
            print(f"Error: HTTP problem while contacting the API ({err})")
        return []
    except requests.exceptions.RequestException as err:
        print(f"Error: could not fetch data from the API ({err})")
        return []
    except ValueError:
        print("Error: API did not return valid JSON.")
        return []

    books = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        title = info.get("title")
        if not title:
            continue  
        author = ", ".join(info.get("authors") or ["Unknown"])
        published = info.get("publishedDate", "")  
        year = int(published[:4]) if published[:4].isdigit() else None
        books.append((title, author, year))
    return books


def init_db(conn):
    """Create the books table if it does not already exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            title            TEXT NOT NULL,
            author           TEXT NOT NULL,
            publication_year INTEGER,
            search_term      TEXT NOT NULL,
            UNIQUE (title, author, search_term)
        )
        """
    )
    conn.commit()


def store_books(conn, books, query):
    """Insert books into the database, skipping duplicates. Returns rows added."""
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO books (title, author, publication_year, search_term) "
        "VALUES (?, ?, ?, ?)",
        [(title, author, year, query) for title, author, year in books],
    )
    conn.commit()
    return conn.total_changes - before


def display_books(conn, query=None):
    """Print stored books as a table. If query is given, show only that search."""
    if query:
        rows = conn.execute(
            "SELECT id, title, author, publication_year FROM books "
            "WHERE search_term = ? ORDER BY id",
            (query,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, author, publication_year FROM books ORDER BY id"
        ).fetchall()

    if not rows:
        print("No books to display.")
        return

    print(f"\n{'ID':<5} {'Title':<45} {'Author':<30} {'Year':<6}")
    print("-" * 88)
    for book_id, title, author, year in rows:
        title = title if len(title) <= 43 else title[:42] + "..."
        author = author if len(author) <= 28 else author[:27] + "..."
        print(f"{book_id:<5} {title:<45} {author:<30} {year if year else 'N/A':<6}")
    print(f"\nTotal books shown: {len(rows)}")


def main():
    if not API_KEY:
        print("Error: GOOGLE_BOOKS_API_KEY environment variable is not set.")
        print('PowerShell example:  $env:GOOGLE_BOOKS_API_KEY="your_key_here"')
        return

    query = input("Enter a search term (e.g. java, history, fantasy): ").strip().lower()
    if not query:
        print("Search term cannot be empty.")
        return

    limit_input = input(f"How many books to fetch? (max {MAX_RESULTS}, default 20): ").strip()
    limit = int(limit_input) if limit_input.isdigit() and int(limit_input) > 0 else 20
    if limit > MAX_RESULTS:
        print(f"Google Books allows at most {MAX_RESULTS} per request; using {MAX_RESULTS}.")
        limit = MAX_RESULTS

    print(f"\nFetching up to {limit} books for '{query}'...")
    books = fetch_books(query, limit)
    print(f"Retrieved {len(books)} books from the API.")

    with sqlite3.connect(DB_NAME) as conn:
        init_db(conn)
        added = store_books(conn, books, query)
        print(f"Stored {added} new books in: {DB_NAME}")

        print(f"\nBooks for '{query}':")
        display_books(conn, query)

if __name__ == "__main__":
    main()