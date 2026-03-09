import requests

base_url = "http://127.0.0.1:8000/api"

# 1. Login to get token with form data!
resp = requests.post(f"{base_url}/auth/login", data={"username": "test@test.com", "password": "password123"})
if resp.status_code != 200:
    print("Attempting registration...")
    requests.post(f"{base_url}/auth/register", json={"email": "test@test.com", "password": "password123", "name": "Test User"})
    resp = requests.post(f"{base_url}/auth/login", data={"username": "test@test.com", "password": "password123"})

token = resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# 2. Check initial account summary
summary1 = requests.get(f"{base_url}/account/summary", headers=headers).json()
print("Initial Summary:", summary1)

# 3. Execute a Trade
trade_payload = {
    "pair": "EUR_USD",
    "direction": "BUY",
    "lot_size": 2.5,
    "sl": 1.0500,
    "tp": 1.1000,
    "confirmed": True
}
exec_resp = requests.post(f"{base_url}/execute", headers=headers, json=trade_payload).json()
print("Execution Result:", exec_resp.get("status"), "PNL:", exec_resp.get("pnl"))

# 4. Check account trades (Journal)
trades = requests.get(f"{base_url}/account/trades", headers=headers).json()
print(f"Journal Trades Count: {len(trades)}")
if len(trades) > 0:
    print(f"Latest Trade: {trades[0].get('pair')} {trades[0].get('direction')} - PNL: {trades[0].get('pnl')}")

# 5. Check updated account summary
summary2 = requests.get(f"{base_url}/account/summary", headers=headers).json()
print("Updated Summary:", summary2)
