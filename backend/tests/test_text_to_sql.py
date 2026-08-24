import pytest
from app.ml.copilot.sql_agent import SQLAgent, SQLValidatorError

@pytest.fixture
def agent():
    return SQLAgent()

def test_sql_validator_valid_select(agent):
    sql = "SELECT amount, merchant FROM transactions WHERE user_id = :user_id"
    provenance = agent._validate_sql(sql)
    assert len(provenance) == 4  # returns the default provenance in our dummy implementation
    
def test_sql_validator_rejects_non_select(agent):
    sql = "UPDATE transactions SET amount = 0 WHERE user_id = :user_id"
    with pytest.raises(SQLValidatorError) as exc:
        agent._validate_sql(sql)
    assert "must be a SELECT" in str(exc.value).upper() or "FORBIDDEN KEYWORD" in str(exc.value).upper()

def test_sql_validator_rejects_drop(agent):
    sql = "DROP TABLE transactions;"
    with pytest.raises(SQLValidatorError) as exc:
        agent._validate_sql(sql)
    assert "FORBIDDEN KEYWORD" in str(exc.value).upper() or "SELECT" in str(exc.value).upper()

def test_sql_validator_rejects_wrong_table(agent):
    sql = "SELECT * FROM users;"
    with pytest.raises(SQLValidatorError) as exc:
        agent._validate_sql(sql)
    assert "TRANSACTIONS" in str(exc.value).upper()
