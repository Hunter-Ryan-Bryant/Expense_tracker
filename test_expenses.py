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