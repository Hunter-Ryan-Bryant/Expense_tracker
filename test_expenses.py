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

    # The expense must actually be gone, not just reported as deleted.
    get_res = client.get(f"/expenses/{expense_id}")
    assert get_res.status_code == 404

    missing_res = client.delete("/expenses/9999")
    assert missing_res.status_code == 404
    assert missing_res.json()["detail"] == "Expense not found"

def test_read_single_expense(client):
    """Test fetching one expense by ID, and a 404 for a missing ID."""
    post_res = client.post("/expenses/", json={"title": "Lunch", "amount": 12.00, "category": "Food", "date_incurred": "2026-10-17"})
    expense_id = post_res.json()["id"]

    get_res = client.get(f"/expenses/{expense_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Lunch"

    assert client.get("/expenses/9999").status_code == 404


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
