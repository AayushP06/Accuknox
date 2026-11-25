import os
import statistics
import matplotlib.pyplot as plt
import requests

API_URL = "http://localhost:8000/db.json"
NAME_FIELD = "name"    # JSON field holding the student's name
SCORE_FIELD = "score"  # JSON field holding the test score

USE_SAMPLE_IF_API_FAILS = True
SAMPLE_DATA = [
    {"name": "Aarav", "score": 78},
    {"name": "Diya", "score": 91},
    {"name": "Kabir", "score": 65},
    {"name": "Meera", "score": 84},
    {"name": "Rohan", "score": 72},
    {"name": "Sneha", "score": 95},
    {"name": "Vikram", "score": 58},
    {"name": "Isha", "score": 88},
]

CHART_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "score_chart.png")


def fetch_students(url):
    """Fetch the JSON records from the API. Returns a list of dicts, or None on failure."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as err:
        print(f"Error: could not fetch data from the API ({err})")
        return None
    except ValueError:
        print("Error: API did not return valid JSON.")
        return None

    
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    return data if isinstance(data, list) else None


def clean_records(records):
    """Keep only records with a name and a numeric score. Returns [(name, score), ...]."""
    students = []
    for record in records:
        name = record.get(NAME_FIELD)
        score = record.get(SCORE_FIELD)
        if name is None or isinstance(score, bool) or not isinstance(score, (int, float)):
            continue  
        students.append((str(name), float(score)))
    return students


def calculate_average(students):
    """Return the average of all scores."""
    return statistics.mean(score for _, score in students)


def plot_scores(students, average):
    """Create a bar chart of the scores with the average shown as a line."""
    names = [name for name, _ in students]
    scores = [score for _, score in students]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(names, scores, color="#4C78A8", edgecolor="black")
    ax.axhline(average, color="red", linestyle="--", linewidth=2,
               label=f"Average: {average:.2f}")

    for bar, score in zip(bars, scores):  
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{score:g}", ha="center", va="bottom", fontsize=9)

    ax.set_title("Students' Test Scores")
    ax.set_xlabel("Student")
    ax.set_ylabel("Score")
    ax.set_ylim(0, max(100, max(scores) + 10))
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    fig.savefig(CHART_FILE, dpi=150)
    print(f"Chart saved to: {CHART_FILE}")
    plt.show()


def main():
    print(f"Fetching data from {API_URL} ...")
    records = fetch_students(API_URL)

    if records is None:
        if not USE_SAMPLE_IF_API_FAILS:
            return
        print("WARNING: using built-in SAMPLE data because the API was unavailable.")
        records = SAMPLE_DATA

    students = clean_records(records)
    if not students:
        print("No valid student records found.")
        return

    average = calculate_average(students)
    highest = max(students, key=lambda s: s[1])
    lowest = min(students, key=lambda s: s[1])

    print(f"\n{'Student':<20} {'Score':>6}")
    print("-" * 27)
    for name, score in students:
        print(f"{name:<20} {score:>6g}")
    print("-" * 27)
    print(f"Students:      {len(students)}")
    print(f"Average score: {average:.2f}")
    print(f"Highest:       {highest[0]} ({highest[1]:g})")
    print(f"Lowest:        {lowest[0]} ({lowest[1]:g})")

    plot_scores(students, average)


if __name__ == "__main__":
    main()