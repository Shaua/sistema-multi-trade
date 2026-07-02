import requests

try:
    res = requests.post("http://localhost:8000/api/backtest", json={
        "asset": "BTC/USD",
        "days": 30,
        "initial_balance": 10000.0
    })
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
except Exception as e:
    print("ERROR:", e)
