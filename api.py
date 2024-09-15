import asyncpg
import os
import asyncio

DATABASE_URL = os.getenv("DATABASE_URL")

async def test_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    version = await conn.fetchval("SELECT version();")
    print(version)
    await conn.close()

asyncio.run(test_connection())