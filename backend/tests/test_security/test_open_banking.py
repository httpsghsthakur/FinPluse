"""Tests for open banking service."""
from app.services.open_banking import OpenBankingService

def test_mock_provider():
    svc = OpenBankingService(provider="mock")
    token = svc.create_link_token("user_1")
    assert "mock-link-user_1" in token
    
    access = svc.exchange_public_token(token)
    assert access.startswith("access-")
    
    txs = svc.sync_transactions(access)
    assert len(txs) > 0
    assert "amount" in txs[0]
