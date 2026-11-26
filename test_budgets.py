from datetime import date

import pytest


def add_expense(client, amount, category, day="2026-10-15", title="Item"):
    res = client.post(
        "/expenses/", json={"title": title, "amount": amount, "category": category, "date_incurred": day}
    )
    assert res.status_code == 201


def set_budget(client, category, limit):
    return client.put(f"/budgets/{category}", json={"monthly_limit": limit})


# ---------- create / update / delete ----------

def test_create_budget_returns_201(client):
    res = set_budget(client, "Food", "200")

    assert res.status_code == 201
    assert res.json() == {"category": "Food", "monthly_limit": "200.00"}


def test_updating_a_budget_returns_200_and_replaces_the_limit(client):
    set_budget(client, "Food", "200")

    res = set_budget(client, "Food", "250.50")

    assert res.status_code == 200
    assert res.json() == {"category": "Food", "monthly_limit": "250.50"}
    assert len(client.get("/budgets?month=2026-10").json()["budgets"]) == 1


def test_budget_categories_are_case_insensitive(client):
    set_budget(client, "food", "100")
    res = set_budget(client, "FOOD", "150")  # same budget, not a second one

    assert res.status_code == 200
    assert res.json()["category"] == "FOOD"  # latest spelling is kept
    assert client.get("/budgets/Food?month=2026-10").json()["monthly_limit"] == "150.00"


def test_category_with_spaces_in_url(client):
    assert set_budget(client, "Eating Out", "80").status_code == 201
    assert client.get("/budgets/eating out?month=2026-10").json()["category"] == "Eating Out"


def test_delete_budget(client):
    set_budget(client, "Food", "200")

    assert client.delete("/budgets/food").status_code == 204
    assert client.get("/budgets/Food").status_code == 404
    assert client.delete("/budgets/Food").status_code == 404


@pytest.mark.parametrize("limit", [0, -5, "1.234", "abc", "100000000.00"])
def test_rejects_bad_limits(client, limit):
    assert set_budget(client, "Food", limit).status_code == 422


def test_rejects_missing_limit(client):
    assert client.put("/budgets/Food", json={}).status_code == 422


@pytest.mark.parametrize("category", ["   ", "x" * 51])
def test_rejects_bad_category_names(client, category):
    assert set_budget(client, category, "10").status_code == 422


def test_missing_budget_is_404(client):
    res = client.get("/budgets/Nope")
    assert res.status_code == 404
    assert res.json()["detail"] == "Budget not found"


# ---------- status for a month ----------

def test_status_spent_and_remaining_are_exact(client):
    set_budget(client, "Food", "200")
    add_expense(client, "0.10", "Food")
    add_expense(client, "0.20", "Food")
    add_expense(client, "49.70", "food")  # case-insensitive match

    res = client.get("/budgets/Food?month=2026-10").json()

    assert res == {
        "category": "Food",
        "month": "2026-10",
        "monthly_limit": "200.00",
        "spent": "50.00",
        "remaining": "150.00",
        "percent_used": 25.0,
        "over_budget": False,
    }


def test_status_only_counts_that_month(client):
    set_budget(client, "Food", "100")
    add_expense(client, 10, "Food", "2026-09-30")
    add_expense(client, 20, "Food", "2026-10-01")  # first day
    add_expense(client, 30, "Food", "2026-10-31")  # last day
    add_expense(client, 40, "Food", "2026-11-01")

    assert client.get("/budgets/Food?month=2026-10").json()["spent"] == "50.00"


def test_status_handles_february_and_leap_years(client):
    set_budget(client, "Food", "100")
    add_expense(client, 5, "Food", "2028-02-29")  # leap day
    add_expense(client, 7, "Food", "2028-03-01")

    assert client.get("/budgets/Food?month=2028-02").json()["spent"] == "5.00"


def test_over_budget(client):
    set_budget(client, "Food", "50")
    add_expense(client, "62.50", "Food")

    res = client.get("/budgets/Food?month=2026-10").json()

    assert res["over_budget"] is True
    assert res["remaining"] == "-12.50"
    assert res["percent_used"] == 125.0


def test_exactly_at_limit_is_not_over(client):
    set_budget(client, "Food", "50")
    add_expense(client, "50.00", "Food")

    res = client.get("/budgets/Food?month=2026-10").json()

    assert res["over_budget"] is False
    assert res["remaining"] == "0.00"
    assert res["percent_used"] == 100.0


def test_percent_used_is_rounded_to_one_decimal(client):
    set_budget(client, "Food", "3")
    add_expense(client, "1", "Food")

    assert client.get("/budgets/Food?month=2026-10").json()["percent_used"] == 33.3


def test_month_defaults_to_current_month(client):
    set_budget(client, "Food", "100")
    add_expense(client, 12, "Food", date.today().isoformat())

    res = client.get("/budgets/Food").json()

    assert res["month"] == date.today().strftime("%Y-%m")
    assert res["spent"] == "12.00"


@pytest.mark.parametrize("month", ["2026-13", "2026-00", "2026-1", "26-10", "October", "2026-10-01"])
def test_rejects_bad_month(client, month):
    set_budget(client, "Food", "100")
    assert client.get(f"/budgets/Food?month={month}").status_code == 422
    assert client.get(f"/budgets?month={month}").status_code == 422


# ---------- overview ----------

def test_overview_with_no_budgets(client):
    add_expense(client, 10, "Food")

    assert client.get("/budgets?month=2026-10").json() == {
        "month": "2026-10",
        "total_limit": "0.00",
        "total_spent": "0.00",
        "total_remaining": "0.00",
        "unbudgeted_spent": "10.00",
        "budgets": [],
    }


def test_overview_totals_and_alphabetical_order(client):
    set_budget(client, "Transport", "100")
    set_budget(client, "Food", "200")
    set_budget(client, "fun", "50")  # sorted case-insensitively
    add_expense(client, "45.25", "Food")
    add_expense(client, "60", "Fun")
    add_expense(client, "30", "Gifts")  # no budget
    add_expense(client, "5", "Food", "2026-11-01")  # different month

    res = client.get("/budgets?month=2026-10").json()

    assert [(b["category"], b["spent"], b["over_budget"]) for b in res["budgets"]] == [
        ("Food", "45.25", False),
        ("fun", "60.00", True),
        ("Transport", "0.00", False),
    ]
    assert res["total_limit"] == "350.00"
    assert res["total_spent"] == "105.25"
    assert res["total_remaining"] == "244.75"
    assert res["unbudgeted_spent"] == "30.00"


def test_budget_named_like_a_route_still_works(client):
    """A category called "status" or "summary" mustn't clash with any route."""
    for name in ["status", "summary", "export.csv"]:
        assert set_budget(client, name, "10").status_code == 201
        assert client.get(f"/budgets/{name}?month=2026-10").json()["category"] == name


def test_deleting_a_budget_keeps_its_expenses(client):
    set_budget(client, "Food", "100")
    add_expense(client, 10, "Food")

    client.delete("/budgets/Food")

    assert len(client.get("/expenses/?category=food").json()) == 1
    assert client.get("/budgets?month=2026-10").json()["unbudgeted_spent"] == "10.00"
