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
    assert response.status_code == 200
    assert data["title"] == "Morning Coffee"
    assert data["amount"] == 4.50
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
    assert data["amount"] == 3.00
    assert data["title"] == "Snack"


def test_delete_expense(client):
    """Test deleting an expense and handling 404 errors."""
    post_res = client.post("/expenses/", json={"title": "Temp Item", "amount": 10.00, "category": "Misc", "date_incurred": "2026-10-17"})
    expense_id = post_res.json()["id"]

    delete_res = client.delete(f"/expenses/{expense_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["ok"] is True

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
    """GET by ID returns the expense, or 404 when it doesn't exist."""
    expense_id = client.post("/expenses/", json={"title": "Book", "amount": 12.00, "category": "School", "date_incurred": "2026-10-17"}).json()["id"]

    response = client.get(f"/expenses/{expense_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Book"

    assert client.get("/expenses/9999").status_code == 404


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
