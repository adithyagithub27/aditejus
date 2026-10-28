"""Tiny expense tracker: reads expenses.csv and prints the total spent."""
import csv


def load(path="expenses.csv"):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def total(rows):
    return sum(int(r["amount"]) for r in rows)


def total_by_category(rows):
    categories = {}
    for r in rows:
        cat = r.get("category", "other")
        if cat not in categories:
            categories[cat] = {"amount": 0}
        categories[cat]["amount"] += int(r["amount"])
    return {cat: t for cat, t in categories.items()}


if __name__ == "__main__":
    rows = load()
    print(f"{len(rows)} expenses")
    totals = total_by_category(rows)
    print(f"by category: {totals}")
    print(f"total Rs {total(rows)}")
