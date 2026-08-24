import httpx
import asyncio

async def test():
    # Login to get token
    async with httpx.AsyncClient() as client:
        res = await client.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'alex.morgan@finpilot.ai', 'password': 'password123'})
        token = res.json().get('access_token')
        print("Token:", bool(token))
        
        # Test CSV import
        csv_data = "Date,Merchant,Amount,Category\n2026-08-15,Whole Foods Market,92.50,cat-groceries"
        res = await client.post(
            'http://127.0.0.1:8000/api/v1/transactions/import',
            headers={'Authorization': f'Bearer {token}'},
            json={'csvText': csv_data}
        )
        print("Status:", res.status_code)
        print("Body:", res.text)

asyncio.run(test())

