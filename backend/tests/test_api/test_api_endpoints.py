"""
FinPilot — Comprehensive API Endpoints Test Suite
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert "status" in res.json()
    assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_accounts(client: AsyncClient):
    res = await client.get("/api/v1/accounts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    assert any(a["id"] == "acc-checking" for a in data)


@pytest.mark.asyncio
async def test_transactions_crud_and_filters(client: AsyncClient):
    # 1. Get transactions list
    res = await client.get("/api/v1/transactions?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "transactions" in data
    assert "total" in data
    assert len(data["transactions"]) == 10

    # 2. Add transaction
    new_tx = {
        "date": "2026-08-18",
        "merchant": "Test Whole Foods Grocery",
        "categoryId": "cat-groceries",
        "accountId": "acc-checking",
        "amount": -65.50,
        "status": "settled",
        "isRecurring": False,
    }
    create_res = await client.post("/api/v1/transactions", json=new_tx)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["merchant"] == "Test Whole Foods Grocery"
    tx_id = created_data["id"]

    # 3. Update transaction
    update_res = await client.patch(f"/api/v1/transactions/{tx_id}", json={"notes": "Updated note"})
    assert update_res.status_code == 200
    assert update_res.json()["notes"] == "Updated note"

    # 4. Search filter
    search_res = await client.get("/api/v1/transactions?search=Test%20Whole%20Foods")
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_budgets_and_goals(client: AsyncClient):
    # Budgets
    bgt_res = await client.get("/api/v1/budgets")
    assert bgt_res.status_code == 200
    bgts = bgt_res.json()
    assert len(bgts) > 0
    assert "predictedSpend" in bgts[0]

    # Goals
    goals_res = await client.get("/api/v1/goals")
    assert goals_res.status_code == 200
    goals = goals_res.json()
    assert len(goals) >= 4

    # Contribute to goal
    g_id = goals[0]["id"]
    contrib_res = await client.post(f"/api/v1/goals/{g_id}/contribute", json={"amount": 100.0})
    assert contrib_res.status_code == 200
    assert contrib_res.json()["currentAmount"] == goals[0]["currentAmount"] + 100.0


@pytest.mark.asyncio
async def test_forecast_and_dashboard(client: AsyncClient):
    # Forecast
    fc_res = await client.get("/api/v1/forecast?days=30")
    assert fc_res.status_code == 200
    fc_data = fc_res.json()
    assert len(fc_data["points"]) > 30
    assert "events" in fc_data

    # Dashboard Summary
    dash_res = await client.get("/api/v1/dashboard/summary")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "netWorth" in dash_data
    assert "cashRunwayMonths" in dash_data
    assert "categorySpend" in dash_data
    assert len(dash_data["upcomingBills"]) > 0


@pytest.mark.asyncio
async def test_simulator_and_copilot(client: AsyncClient):
    # Simulator
    scenario = {
        "name": "New Laptop + 10% raise",
        "incomeChangePct": 10.0,
        "oneTimeExpense": 2500.0,
        "monthlySavingsChange": 200.0,
        "expenseCutPct": 0.0,
        "monthsWithoutIncome": 0,
    }
    sim_res = await client.post("/api/v1/simulator/run", json=scenario)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert "monthlyPoints" in sim_data
    assert len(sim_data["monthlyPoints"]) == 13
    assert "goalImpacts" in sim_data

    # Copilot Chat
    from unittest.mock import AsyncMock, patch
    with patch("app.api.v1.copilot.sql_agent.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {
            "sql": "SELECT * FROM transactions",
            "results": [{"amount": -500}],
            "explanation": "Yes, you can afford it.",
            "data_provenance": ["transactions"]
        }
        chat_res = await client.post("/api/v1/copilot/chat", json={"message": "Can I afford a $500 flight?"})
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "content" in chat_data
    assert "groundedData" in chat_data
    assert len(chat_data["groundedData"]) > 0
