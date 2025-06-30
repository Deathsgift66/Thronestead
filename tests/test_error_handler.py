import json
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.main import app


@app.get("/__raise")
def raise_http_exc():
    raise HTTPException(status_code=401, detail="nope")


def test_http_exception_passthrough():
    client = TestClient(app)
    resp = client.get("/__raise")
    assert resp.status_code == 401
    data = json.loads(resp.text)
    assert data["detail"] == "nope"
