from backend.routers.alliance_vault import custom_router


def test_custom_router_prefix():
    assert custom_router.prefix == "/api/alliance/custom/vault"
