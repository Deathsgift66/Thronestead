import json
from fastapi.testclient import TestClient
from backend.main import app
import backend.routers.ban_appeal as ban_appeal

client = TestClient(app)


def test_ban_appeal(monkeypatch):
    monkeypatch.setattr(ban_appeal, 'verify_hcaptcha', lambda t, remote_ip=None: True)
    captured = {}
    def fake_send(to, subject, body):
        captured['to'] = to
        captured['subject'] = subject
        captured['body'] = body
    monkeypatch.setattr(ban_appeal, 'send_email', fake_send)

    resp = client.post('/api/ban/appeal', json={
        'email': 'user@example.com',
        'message': 'please unban',
        'captcha_token': 'x'
    })
    assert resp.status_code == 200
    assert captured['to'] == 'thronestead@gmail.com'
    assert 'please unban' in captured['body']
