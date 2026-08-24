import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        # Create a new user so we can test the exact flow of a new user
        res = await client.post('http://127.0.0.1:8000/api/v1/auth/signup', json={'email': 'newuser123@example.com', 'password': 'password123', 'name': 'New User'})
        if res.status_code == 404:
            print("Signup 404, using login...")
            res = await client.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'alex.morgan@finpilot.ai', 'password': 'password123'})
        
        # We don't have a reliable way to get token without Supabase Auth in this environment
        # Wait, how does local dev auth work without Supabase?
        print(res.text)

asyncio.run(test())
