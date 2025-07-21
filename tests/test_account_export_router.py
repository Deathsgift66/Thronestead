import io
import json
import zipfile

from backend.models import User, Kingdom, PlayerMessage, AuditLog, KingdomTroop
from backend.routers import account_export


def seed_data(db):
    user = User(
        user_id="u1",
        username="player",
        email="p@example.com",
        kingdom_id=1,
        kingdom_name="kingdom",
    )
    kingdom = Kingdom(kingdom_id=1, user_id="u1", kingdom_name="Camelot")
    msg = PlayerMessage(user_id="u1", recipient_id="u1", message="Hi")
    log = AuditLog(user_id="u1", action="login", details="ok")
    troop = KingdomTroop(kingdom_id=1, unit_type="infantry", unit_level=1, quantity=5)
    db.add_all([user, kingdom, msg, log, troop])
    db.commit()


def test_export_contains_user_data(db_session):
    seed_data(db_session)
    response = account_export.export_account(user_id="u1", db=db_session)
    assert (
        response.headers.get("Content-Disposition")
        == "attachment; filename=account_export.zip"
    )
    assert response.media_type == "application/zip"
    z = zipfile.ZipFile(io.BytesIO(response.body))
    data = json.loads(z.read("data.json").decode())
    assert data["user"]["user_id"] == "u1"
    assert data["kingdom"]["kingdom_name"] == "Camelot"
    assert data["messages"][0]["message"] == "Hi"
    assert data["audit_logs"][0]["action"] == "login"
    assert data["troops"][0]["quantity"] == 5

