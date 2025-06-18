from backend.routers import tokens

class DummyDB:
    pass


def test_redeem_calls_services(monkeypatch):
    calls = {}

    def dummy_consume(db, uid, amt):
        calls['consume'] = amt
        return True

    def dummy_upsert(db, uid, level, expires):
        calls['upsert'] = level

    monkeypatch.setattr(tokens, 'consume_tokens', dummy_consume)
    monkeypatch.setattr(tokens, 'upsert_vip_status', dummy_upsert)

    result = tokens.redeem_tokens(tokens.RedeemPayload(perk_id='vip1'), user_id='u1', db=DummyDB())
    assert result['perk'] == 'vip1'
    assert calls['consume'] == 1
    assert calls['upsert'] == 1

