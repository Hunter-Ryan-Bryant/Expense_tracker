import pytest


def test_create_expense(client):
    """Test creating a new expense via POST."""
    response = client.post(
        "/expenses/",
        json={
            "title": "Morning Coffee",
            "amount": 4.50,
            "category": "Food",
            "date_incurred": "2026-10-17"
        }
    )
    data = response.json()
    assert response.status_code == 201
    assert data["title"] == "Morning Coffee"
    assert data["amount"] == "4.50"  # money is sent as an exact 2-decimal string
    assert "id" in data


def test_read_expenses_with_filter(client):
    """Test retrieving expenses and filtering by category."""
    client.post("/expenses/", json={"title": "Latte", "amount": 5.00, "category": "Food", "date_incurred": "2026-10-17"})
    client.post("/expenses/", json={"title": "Gas", "amount": 40.00, "category": "Transport", "date_incurred": "2026-10-17"})

    response = client.get("/expenses/?category=Food")
    data = response.json()
    
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Latte"


def test_update_expense(client):
    """Test partial updates using PATCH."""
    post_res = client.post("/expenses/", json={"title": "Snack", "amount": 2.50, "category": "Food", "date_incurred": "2026-10-17"})
    expense_id = post_res.json()["id"]

    patch_res = client.patch(
        f"/expenses/{expense_id}",
        json={"amount": 3.00}
    )
    data = patch_res.json()
    
    assert patch_res.status_code == 200
    assert data["amount"] == "3.00"
    assert data["title"] == "Snack"


def test_delete_expense(client):
    """Test deleting an expense and handling 404 errors."""
    post_res = client.post("/expenses/", json={"title": "Temp Item", "amount": 10.00, "category": "Misc", "date_incurred": "2026-10-17"})
    expense_id = post_res.json()["id"]

    delete_res = client.delete(f"/expenses/{expense_id}")
    assert delete_res.status_code == 204
    assert delete_res.content == b""

    # The expense must actually be gone, not just reported as deleted.
    get_res = client.get(f"/expenses/{expense_id}")
    assert get_res.status_code == 404

    missing_res = client.delete("/expenses/9999")
    assert missing_res.status_code == 404
    assert missing_res.json()["detail"] == "Expense not found"


def test_deleted_expense_is_gone(client):
    """A deleted expense can no longer be fetched or listed."""
    expense_id = client.post("/expenses/", json={"title": "Old", "amount": 1.00, "category": "Misc", "date_incurred": "2026-10-17"}).json()["id"]

    client.delete(f"/expenses/{expense_id}")

    assert client.get(f"/expenses/{expense_id}").status_code == 404
    assert client.get("/expenses/").json() == []


def test_read_single_expense(client):
    """GET by ID returns the full expense, or 404 when it doesn't exist."""
    post_res = client.post("/expenses/", json={"title": "Lunch", "amount": 12.00, "category": "Food", "date_incurred": "2026-10-17"})
    expense_id = post_res.json()["id"]

    get_res = client.get(f"/expenses/{expense_id}")
    assert get_res.status_code == 200
    assert get_res.json() == post_res.json()

    missing_res = client.get("/expenses/9999")
    assert missing_res.status_code == 404
    assert missing_res.json()["detail"] == "Expense not found"


def test_date_range_sorting_and_pagination(client):
    """Filter by date range, sort by amount, and page through results."""
    for title, amount, day in [("A", 5.0, "2026-10-01"), ("B", 20.0, "2026-10-10"), ("C", 10.0, "2026-10-20"), ("D", 1.0, "2026-11-05")]:
        client.post("/expenses/", json={"title": title, "amount": amount, "category": "Food", "date_incurred": day})

    in_october = client.get("/expenses/?start_date=2026-10-01&end_date=2026-10-31").json()
    assert {e["title"] for e in in_october} == {"A", "B", "C"}

    by_amount = client.get("/expenses/?sort_by=amount&order=asc").json()
    assert [e["title"] for e in by_amount] == ["D", "A", "C", "B"]

    page_two = client.get("/expenses/?sort_by=amount&order=asc&limit=2&offset=2").json()
    assert [e["title"] for e in page_two] == ["C", "B"]


def test_rejects_non_positive_amount(client):
    """Amounts must be greater than zero on create and on update."""
    bad_create = client.post("/expenses/", json={"title": "Refund?", "amount": -5.00})
    assert bad_create.status_code == 422

    post_res = client.post("/expenses/", json={"title": "Book", "amount": 20.00})
    expense_id = post_res.json()["id"]
    bad_update = client.patch(f"/expenses/{expense_id}", json={"amount": 0})
    assert bad_update.status_code == 422


def test_sort_by_amount_and_date_range(client):
    """Test sorting by amount and filtering by a date range."""
    client.post("/expenses/", json={"title": "Small", "amount": 1.00, "date_incurred": "2026-10-01"})
    client.post("/expenses/", json={"title": "Big", "amount": 100.00, "date_incurred": "2026-10-15"})
    client.post("/expenses/", json={"title": "Old", "amount": 50.00, "date_incurred": "2025-01-01"})

    asc_res = client.get("/expenses/?sort_by=amount&order=asc&start_date=2026-01-01")
    titles = [e["title"] for e in asc_res.json()]
    assert titles == ["Small", "Big"]


# ---------- exact money ----------

def test_amounts_are_exact_two_decimal_strings(client):
    """0.10 and 0.20 stay exact instead of drifting like floats (0.1 + 0.2 != 0.3)."""
    a = client.post("/expenses/", json={"title": "A", "amount": 0.1}).json()
    b = client.post("/expenses/", json={"title": "B", "amount": "0.20"}).json()

    assert a["amount"] == "0.10"
    assert b["amount"] == "0.20"


def test_amounts_accept_numbers_and_strings(client):
    assert client.post("/expenses/", json={"title": "Num", "amount": 4.5}).status_code == 201
    assert client.post("/expenses/", json={"title": "Str", "amount": "4.50"}).status_code == 201


@pytest.mark.parametrize("amount", [4.555, "0.001", "100000000.00", "abc"])
def test_rejects_bad_amounts(client, amount):
    """More than 2 decimals, over 10 digits, or not a number."""
    assert client.post("/expenses/", json={"title": "Bad", "amount": amount}).status_code == 422


# ---------- text fields ----------

@pytest.mark.parametrize("field", ["title", "category"])
@pytest.mark.parametrize("value", ["", "   "])
def test_rejects_empty_text(client, field, value):
    body = {"title": "Lunch", "amount": 10, "category": "Food", field: value}
    assert client.post("/expenses/", json=body).status_code == 422


def test_text_is_trimmed(client):
    data = client.post("/expenses/", json={"title": "  Lunch  ", "amount": 10, "category": " Food "}).json()
    assert data["title"] == "Lunch"
    assert data["category"] == "Food"


# ---------- PATCH ----------

@pytest.mark.parametrize("field", ["title", "amount", "category", "date_incurred"])
def test_patch_rejects_null_and_leaves_record_unchanged(client, field):
    """Sending null used to crash the server with a 500."""
    created = client.post("/expenses/", json={"title": "Keep", "amount": 5, "category": "Food", "date_incurred": "2026-10-17"}).json()

    res = client.patch(f"/expenses/{created['id']}", json={field: None})

    assert res.status_code == 422
    assert client.get(f"/expenses/{created['id']}").json() == created


def test_patch_rejects_empty_title(client):
    expense_id = client.post("/expenses/", json={"title": "Keep", "amount": 5}).json()["id"]
    assert client.patch(f"/expenses/{expense_id}", json={"title": "  "}).status_code == 422


def test_patch_missing_expense_is_404(client):
    assert client.patch("/expenses/9999", json={"amount": 1}).status_code == 404


# ---------- list query parameters ----------

@pytest.mark.parametrize(
    "query",
    [
        "sort_by=amout",
        "sort_by=title",
        "order=up",
        "limit=0",
        "limit=-1",
        "limit=501",
        "offset=-1",
    ],
)
def test_list_rejects_bad_query_params(client, query):
    assert client.get(f"/expenses/?{query}").status_code == 422


def test_list_rejects_reversed_date_range(client):
    res = client.get("/expenses/?start_date=2026-10-31&end_date=2026-10-01")
    assert res.status_code == 422
    assert res.json()["detail"] == "start_date must be on or before end_date"


def test_category_filter_ignores_case(client):
    client.post("/expenses/", json={"title": "Latte", "amount": 5, "category": "Food"})
    client.post("/expenses/", json={"title": "Gas", "amount": 40, "category": "Transport"})

    for query in ["food", "FOOD", "Food", " food "]:
        titles = [e["title"] for e in client.get("/expenses/", params={"category": query}).json()]
        assert titles == ["Latte"], query


def test_pagination_is_stable_when_amounts_tie(client):
    ids = [client.post("/expenses/", json={"title": f"T{i}", "amount": 5}).json()["id"] for i in range(5)]

    page1 = client.get("/expenses/?sort_by=amount&order=asc&limit=2").json()
    page2 = client.get("/expenses/?sort_by=amount&order=asc&limit=2&offset=2").json()
    page3 = client.get("/expenses/?sort_by=amount&order=asc&limit=2&offset=4").json()

    assert [e["id"] for e in page1 + page2 + page3] == ids


# ---------- setup ----------

def test_tests_never_touch_the_real_database():
    import database

    assert database.engine.url.database in (None, "", ":memory:")


# ---------- summary ----------

def add(client, title, amount, category="General", day="2026-10-15"):
    res = client.post("/expenses/", json={"title": title, "amount": amount, "category": category, "date_incurred": day})
    assert res.status_code == 201
    return res.json()


def test_summary_when_empty(client):
    res = client.get("/expenses/summary")

    assert res.status_code == 200
    assert res.json() == {
        "group_by": "category",
        "q": None,
        "category": None,
        "start_date": None,
        "end_date": None,
        "total": "0.00",
        "count": 0,
        "groups": [],
    }


def test_summary_by_category_is_exact_and_sorted_by_total(client):
    add(client, "Coffee", "0.10", "Food")
    add(client, "Snack", "0.20", "Food")
    add(client, "Gas", "40.00", "Transport")
    add(client, "Book", "12.50", "School")

    data = client.get("/expenses/summary").json()

    assert data["total"] == "52.80"
    assert data["count"] == 4
    assert data["groups"] == [
        {"key": "Transport", "total": "40.00", "count": 1},
        {"key": "School", "total": "12.50", "count": 1},
        {"key": "Food", "total": "0.30", "count": 2},  # exact: floats would give 0.30000000000000004
    ]


def test_summary_ties_are_sorted_by_name(client):
    add(client, "B", 5, "Beta")
    add(client, "A", 5, "alpha")

    keys = [g["key"] for g in client.get("/expenses/summary").json()["groups"]]
    assert keys == ["alpha", "Beta"]


def test_summary_groups_categories_case_insensitively(client):
    add(client, "Latte", 5, "Food")
    add(client, "Bagel", 3, "food")
    add(client, "Tea", 2, "FOOD")

    groups = client.get("/expenses/summary").json()["groups"]

    assert groups == [{"key": "Food", "total": "10.00", "count": 3}]  # first-used spelling


def test_summary_by_month_in_date_order(client):
    add(client, "Nov", 7, day="2026-11-02")
    add(client, "Sep", 1, day="2026-09-30")
    add(client, "Oct A", 2, day="2026-10-01")
    add(client, "Oct B", 3, day="2026-10-31")

    data = client.get("/expenses/summary?group_by=month").json()

    assert data["group_by"] == "month"
    assert data["groups"] == [
        {"key": "2026-09", "total": "1.00", "count": 1},
        {"key": "2026-10", "total": "5.00", "count": 2},
        {"key": "2026-11", "total": "7.00", "count": 1},
    ]


def test_summary_answers_food_in_october(client):
    """How much did I spend on food in October?"""
    add(client, "Latte", "4.50", "Food", "2026-10-03")
    add(client, "Lunch", "12.25", "Food", "2026-10-20")
    add(client, "Late lunch", "9.00", "Food", "2026-11-01")  # outside the range
    add(client, "Gas", "40.00", "Transport", "2026-10-10")  # other category

    data = client.get(
        "/expenses/summary", params={"category": "food", "start_date": "2026-10-01", "end_date": "2026-10-31"}
    ).json()

    assert data["total"] == "16.75"
    assert data["count"] == 2
    assert data["category"] == "food"
    assert data["start_date"] == "2026-10-01"
    assert data["end_date"] == "2026-10-31"


@pytest.mark.parametrize("query", ["group_by=week", "group_by=", "start_date=2026-10-31&end_date=2026-10-01"])
def test_summary_rejects_bad_query_params(client, query):
    assert client.get(f"/expenses/summary?{query}").status_code == 422


def test_summary_route_does_not_break_get_by_id(client):
    """/expenses/summary must not be treated as /expenses/{id}, and vice versa."""
    expense = add(client, "Lunch", 12)

    assert client.get("/expenses/summary").status_code == 200
    assert client.get(f"/expenses/{expense['id']}").json() == expense


# ---------- search ----------

def titles(client, **params):
    res = client.get("/expenses/", params={"sort_by": "amount", "order": "asc", **params})
    assert res.status_code == 200
    return [e["title"] for e in res.json()]


def test_search_matches_part_of_title_ignoring_case(client):
    add(client, "Morning Coffee", 4.5)
    add(client, "coffee beans", 12)
    add(client, "Iced COFFEE", 6)
    add(client, "Tea", 3)

    assert titles(client, q="coffee") == ["Morning Coffee", "Iced COFFEE", "coffee beans"]
    assert titles(client, q="CoFf") == ["Morning Coffee", "Iced COFFEE", "coffee beans"]
    assert titles(client, q="ning cof") == ["Morning Coffee"]


def test_search_with_no_matches(client):
    add(client, "Tea", 3)
    assert titles(client, q="pizza") == []


def test_blank_search_is_ignored(client):
    add(client, "Tea", 3)
    add(client, "Coffee", 4)

    assert titles(client, q="") == ["Tea", "Coffee"]
    assert titles(client, q="   ") == ["Tea", "Coffee"]


def test_search_text_is_trimmed(client):
    add(client, "Coffee", 4)
    assert titles(client, q="  coffee  ") == ["Coffee"]


@pytest.mark.parametrize(
    "q, expected",
    [
        ("%", ["50% off sale"]),  # % is literal, not "match anything"
        ("_", ["file_name"]),  # _ is literal, not "any one character"
        ("\\", ["back\\slash"]),
        ("50%", ["50% off sale"]),
    ],
)
def test_search_treats_wildcards_literally(client, q, expected):
    add(client, "50% off sale", 1)
    add(client, "file_name", 2)
    add(client, "back\\slash", 3)
    add(client, "plain", 4)

    assert titles(client, q=q) == expected


def test_search_combines_with_other_filters(client):
    add(client, "Coffee", 4, "Food", "2026-10-05")
    add(client, "Coffee", 5, "Food", "2026-11-05")  # wrong month
    add(client, "Coffee maker", 60, "Home", "2026-10-06")  # wrong category
    add(client, "Bagel", 3, "Food", "2026-10-07")  # doesn't match

    res = client.get(
        "/expenses/",
        params={"q": "coffee", "category": "food", "start_date": "2026-10-01", "end_date": "2026-10-31"},
    ).json()

    assert [(e["title"], e["amount"]) for e in res] == [("Coffee", "4.00")]


def test_search_is_limited_to_100_characters(client):
    assert client.get("/expenses/", params={"q": "x" * 100}).status_code == 200
    assert client.get("/expenses/", params={"q": "x" * 101}).status_code == 422


def test_summary_supports_search(client):
    """How much have I spent on coffee?"""
    add(client, "Morning Coffee", "4.50", "Food")
    add(client, "Coffee beans", "12.25", "Groceries")
    add(client, "Tea", "3.00", "Food")

    data = client.get("/expenses/summary", params={"q": "coffee"}).json()

    assert data["q"] == "coffee"
    assert data["total"] == "16.75"
    assert data["count"] == 2
    assert data["groups"] == [
        {"key": "Groceries", "total": "12.25", "count": 1},
        {"key": "Food", "total": "4.50", "count": 1},
    ]
