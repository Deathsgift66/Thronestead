from backend.routers import missing_api as api


def test_declare_battle():
    res = api.declare_battle(api.BattleDeclarePayload(target_id="k2"), user_id="u1")
    assert res["status"] == "pending"


def test_update_account():
    res = api.update_account(api.AccountUpdatePayload(field="name", value="X"), user_id="u1")
    assert res["status"] == "updated"


def test_create_event():
    res = api.create_event(api.AdminEventPayload(name="E"), user_id="u1")
    assert res["status"] == "created"


def test_update_kingdom_field():
    res = api.update_kingdom_field(
        api.AdminFieldPayload(kingdom_id=1, field="motto", value="Hi"),
        user_id="u1",
    )
    assert res["status"] == "updated"


def test_system_rollback():
    res = api.system_rollback(api.RollbackPayload(password="pw"), user_id="u1")
    assert res["status"] == "queued"


def test_alliance_vault_board():
    assert api.alliance_vault_board() == {"board": []}


def test_alliance_custom_vault():
    assert api.alliance_custom_vault() == {"vault": []}


def test_propose_treaty():
    res = api.propose_treaty(
        api.TreatyProposal(partner_alliance_id=2, treaty_type="trade"),
        user_id="u1",
    )
    assert res["status"] == "proposed"


def test_battle_history():
    assert api.battle_history() == {"history": []}


def test_battle_orders():
    res = api.battle_orders(api.BattleOrdersPayload(war_id=1, orders=[]), user_id="u1")
    assert res["status"] == "received"


def test_battle_wars():
    assert api.battle_wars() == {"wars": []}


def test_black_market_listings():
    assert api.black_market_listings() == {"listings": []}


def test_black_market_purchase():
    res = api.black_market_purchase(api.PurchasePayload(listing_id=1, quantity=1), user_id="u1")
    assert res["status"] == "purchased"


def test_conflicts_all():
    assert api.conflicts_all() == {"conflicts": []}


def test_kingdom_troops_unlocked():
    assert api.kingdom_troops_unlocked() == {"troops": []}


def test_castle_upgrade():
    res = api.castle_upgrade(user_id="u1")
    assert res["status"] == "queued"


def test_promote_knight():
    res = api.promote_knight(api.KnightName(name="A"), user_id="u1")
    assert res["status"] == "promoted"


def test_rename_knight():
    res = api.rename_knight(api.KnightName(name="A"), user_id="u1")
    assert res["status"] == "renamed"


def test_rename_noble():
    res = api.rename_noble(api.KnightName(name="A"), user_id="u1")
    assert res["status"] == "renamed"

