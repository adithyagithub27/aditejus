"""Tiny expense tracker: reads expenses.csv and prints the total spent."""
import csv


def load(path="expenses.csv"):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def total(rows):
    return sum(int(r["amount"]) for r in rows)


if __name__ == "__main__":
    rows = load()
    print(f"{len(rows)} expenses, total Rs {total(rows)}")
