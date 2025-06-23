from backend.routers import tokens


class DummyDB:
    pass


def test_redeem_calls_services(monkeypatch):
    calls = {}

    def dummy_consume(db, uid, amt):
        calls["consume"] = amt
        return True

    def dummy_upsert(db, uid, level, expires):
        calls["upsert"] = level

    monkeypatch.setattr(tokens, "consume_tokens", dummy_consume)
    monkeypatch.setattr(tokens, "upsert_vip_status", dummy_upsert)

    result = tokens.redeem_tokens(
        tokens.RedeemPayload(perk_id="vip1"), user_id="u1", db=DummyDB()
    )
    assert result["perk"] == "vip1"
    assert calls["consume"] == 1
    assert calls["upsert"] == 1


def test_balance_includes_metadata(monkeypatch):
    def dummy_get(db, uid):
        return 5

    monkeypatch.setattr(tokens, "get_balance", dummy_get)

    data = tokens.token_balance(user_id="u1", db=DummyDB())
    assert data["tokens"] == 5
    assert data["stealable"] is False
    assert data["expires"] is False


def test_buy_tokens(monkeypatch):
    calls = {}

    def dummy_add(db, uid, amt):
        calls["add"] = amt

    monkeypatch.setattr(tokens, "add_tokens", dummy_add)

    result = tokens.buy_tokens(
        tokens.BuyPayload(package_id=1), user_id="u1", db=DummyDB()
    )
    assert result["tokens"] == tokens.TOKEN_PACKAGES[1]
    assert calls["add"] == tokens.TOKEN_PACKAGES[1]
