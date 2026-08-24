import pytest
from app.services.open_banking import OpenBankingService

def test_mock_open_banking():
    service = OpenBankingService(provider="mock")
    
    token = service.create_link_token("user123")
    assert "mock-link-user123" in token
    
    access = service.exchange_public_token("pub_token")
    assert access == "access-pub_token"
    
    txs = service.sync_transactions(access)
    assert len(txs) == 20
    assert "amount" in txs[0]
