import sys
print("-> Python is running the script!", flush=True)

try:
    import requests
    print("-> 'requests' module imported successfully.", flush=True)
except ImportError as e:
    print(f"-> ERROR: Could not import requests: {e}", flush=True)
    sys.exit(1)

BASE_URL = "http://127.0.0.1:8000"

def test_expense_tracker():
    print("--- Testing FastAPI Expense Tracker ---", flush=True)
    
    payload = {
        "title": "Morning Coffee",
        "amount": 4.50,
        "category": "Food",
        "date_incurred": "2026-10-13"
    }
    
    print(f"\n[POST] Sending payload to {BASE_URL}/expenses/...", flush=True)
    try:
        # Added a 5-second timeout so it never hangs silently
        post_response = requests.post(f"{BASE_URL}/expenses/", json=payload, timeout=5)
    except requests.exceptions.Timeout:
        print("[Error] The request timed out. Is Uvicorn blocked or hung?")
        return
    except requests.exceptions.ConnectionError:
        print("[Error] Connection refused. Make sure Uvicorn is running on http://127.0.0.1:8000!")
        return

    print(f"Status Code: {post_response.status_code}", flush=True)
    print(f"Response Body: {post_response.json()}", flush=True)

if __name__ == "__main__":
    test_expense_tracker()