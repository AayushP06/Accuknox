# Python & SQLite Assignments

Three self-contained Python scripts covering REST API consumption, data visualization, and CSV-to-SQLite ingestion.

## Project Structure

```text
.
├── books_api.py       # Assignment 1 – Google Books API -> SQLite
├── student_scores.py  # Assignment 2 – Mock REST API -> Matplotlib bar chart
├── db.json            # Assignment 2 – Student dataset served as a mock API
├── csv_to_sqlite.py   # Assignment 3 – CSV validation & bulk import -> SQLite
├── customers.csv      # Assignment 3 – Sample dataset (1,000 synthetic rows)
└── README.md
```

**Generated outputs** (created in the project folder when each script runs):

- `books.db` (Assignment 1)
- `score_chart.png` (Assignment 2)
- `users.db` (Assignment 3)

## Requirements

- **Python 3.8+**
- Third-party packages:

```bash
pip install requests matplotlib
```

> `sqlite3`, `csv`, `re`, `statistics`, `os`, and `sys` are part of the Python standard library.

---

## Assignment 1 – API Data Retrieval and Storage

**Goal:** Fetch a list of books (`title`, `author`, `publication_year`) from an external REST API, store them in a local SQLite database, and display the stored records.

### API & Configuration

- **API used:** [Google Books Volumes API](https://www.googleapis.com/books/v1/volumes) (`https://www.googleapis.com/books/v1/volumes`)
- **Why this API:** Returns structured JSON with `title`, `authors`, and `publishedDate` in a single request and supports query/limit parameters (`maxResults` up to `40`).
- **API Key:** Required via the `GOOGLE_BOOKS_API_KEY` environment variable (to avoid unauthenticated shared-quota `429 Too Many Requests` errors).

Set your API key before running:

```powershell
# PowerShell
$env:GOOGLE_BOOKS_API_KEY="your_api_key_here"
```

```bash
# macOS / Linux (bash/zsh)
export GOOGLE_BOOKS_API_KEY="your_api_key_here"
```

### How It Works

1. Prompts for a search term (e.g., `java`, `history`, `fantasy`) and the number of books to fetch (default `20`, max `40`).
2. Sends a `GET` request via `requests` and extracts `title`, `authors` (joined as a comma-separated string, defaulting to `"Unknown"`), and the 4-digit year from `publishedDate` (or `None`, displayed as `N/A`).
3. Creates `books.db` with table `books (id, title, author, publication_year, search_term)` and a `UNIQUE (title, author, search_term)` constraint.
4. Inserts records using parameterized queries (`?` placeholders) and `INSERT OR IGNORE` so repeated runs do not create duplicates.
5. Queries and prints the stored books for that search term as a formatted table.

### Run

```bash
python books_api.py
```

## Assignment 2 – Data Processing and Visualization

**Goal:** Fetch students' test scores from a REST API, calculate summary statistics (including the average score), and plot a bar chart.

### API & Configuration

- **API used:** A mock REST endpoint serving `db.json` (no well-known public API provides student test scores, so `db.json` lets the script make a real HTTP call without keys or signup).
- **Expected JSON shape:**

```json
{
  "students": [{ "id": 1, "name": "Aarav", "score": 78 }]
}
```

`API_URL` at the top of `student_scores.py` defaults to `http://localhost:8000/db.json`. You can use either option:

- **Local server (default):** Start Python's built-in HTTP server in the project folder:
  ```bash
  python -m http.server 8000
  ```
- **GitHub-hosted mock API:** Push `db.json` to GitHub and set `API_URL` to:
  ```text
  https://my-json-server.typicode.com/<your-username>/<your-repo>/students
  ```

> **Extensibility:** The script accepts either a JSON list or an object wrapping a list, and field names can be changed via `NAME_FIELD` and `SCORE_FIELD` in `student_scores.py`.

### How It Works

1. Fetches JSON data from `API_URL` with `requests`.
2. Cleans records by skipping entries with a missing name or non-numeric score (explicitly rejecting booleans).
3. Computes the mean (`statistics.mean`), highest score, and lowest score, then prints a summary table.
4. Generates a Matplotlib bar chart with value labels on each bar and a red dashed horizontal line marking the average.
5. Saves the chart to `score_chart.png` (150 DPI) and displays it.

### Run

```bash
# Terminal 1: serve db.json locally
python -m http.server 8000

# Terminal 2: run the script
python student_scores.py
```

> **Fallback behavior:** If the API cannot be reached, the script prints a warning and falls back to built-in `SAMPLE_DATA`. Set `USE_SAMPLE_IF_API_FAILS = False` in `student_scores.py` to fail fast instead.

---

## Assignment 3 – CSV Data Import to a Database

**Goal:** Read user records (`name`, `email`) from a CSV file, validate them, and bulk-insert them into a SQLite database.

### Dataset

- **Sample file:** `customers.csv` (1,000 synthetic customer records from [Sling Academy](https://api.slingacademy.com/v1/sample-data/files/customers.csv)).
- **Columns:** `first_name`, `last_name`, `email`, `phone`, `address`, `is_married`.
- **Why this dataset:** Synthetic data (no privacy concerns), large enough to exercise bulk insertion and validation, and maps cleanly to `name` and `email`.

### How It Works

1. Reads the CSV file using `csv.DictReader` (`utf-8-sig` encoding) and normalizes column headers case-insensitively.
2. Accepts either a `name` column or combines `first_name` + `last_name` into a full name; ignores extra columns.
3. Validates each row (non-empty name and email matching `^[^@\s]+@[^@\s]+\.[^@\s]+$`, lowercased). Invalid rows are skipped with their line number and reason logged.
4. Bulk-inserts valid rows into `users.db`, table `users (id, name, email UNIQUE)`, using `executemany` and `INSERT OR IGNORE`.
5. Prints a summary (valid rows read, skipped rows, new rows inserted, duplicate emails ignored) and displays the stored users table.

### Run

```bash
python csv_to_sqlite.py customers.csv
```

> If no file argument is passed, the script defaults to `users.csv` in the same directory.
