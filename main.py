import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from together import Together
from typing import List

# Load environment variables
load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)
# FastAPI app initialization
app = FastAPI()

# Pydantic model for data validation
class ItemSearch(BaseModel):
    userid: str
    searchitem: str
    minprice: float
    maxprice: float

class ItemCreate(BaseModel):
    description: str
    searchid: int
    url: str
    image: str
    message: str
    itemsearch: str
    listedprice: float
    estimateprice: float
    minprice: float
    maxprice: float

class ChatRequest(BaseModel):
    message: str
    chat_history: list = []

class ChatResponse(BaseModel):
    response: str
# Lifespan context manager for resource management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize asyncpg connection pool
    app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)
    yield
    # Clean up (close connection pool) when app shuts down
    await app.state.db_pool.close()

# FastAPI app initialization with lifespan
app = FastAPI(lifespan=lifespan)

# Test connection endpoint
@app.get("/test_db")
async def test_db():
    try:
        conn = await app.state.db_pool.acquire()
        version = await conn.fetchval("SELECT version();")
        await app.state.db_pool.release(conn)
        return {"PostgreSQL Version": version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# Create new item in the database
@app.post("/searchItems", response_model=dict)
async def search_item(item: ItemSearch):
    try:
        print(item)
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item_search (userid, searchitem, minprice, maxprice)
            VALUES ($1, $2, $3, $4)
            RETURNING id, userid, searchitem, minprice, maxprice
        """
        result = await conn.fetchrow(query, item.userid, item.searchitem, item.minprice, item.maxprice)
        await app.state.db_pool.release(conn)
        return {
            "id": result["id"],
            "userid": result["userid"],
            "searchitem": result["searchitem"],
            "minprice": result["minprice"],
            "maxprice": result["maxprice"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {e}")


@app.post("/addItem", response_model=dict)
async def create_item(item: ItemCreate):
    try:
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice
        """
        result = await conn.fetchrow(query, item.description, item.searchid, item.url, item.image, item.message, item.itemsearch, item.listedprice, item.estimateprice, item.minprice, item.maxprice)
        await app.state.db_pool.release(conn)
        return {
            "id": result["id"],
            "description": result["description"],
            "searchid": result["searchid"],
            "url": result["url"],
            "image": result["image"],
            "message": result["message"],
            "itemsearch": result["itemsearch"],
            "listedprice": result["listedprice"],
            "estimateprice": result["estimateprice"],
            "minprice": result["minprice"],
            "maxprice": result["maxprice"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {e}")
        
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        messages = request.chat_history + [{"role": "user", "content": request.message}]

        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            messages=messages,
            max_tokens=4096,
            temperature=0.3
        )
        print(completion.choices[0].message.content)
        return ChatResponse(response=completion.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class shortItem(BaseModel):
    description: str
    imageUrl: str
    url: str
    price: float
    
class shortItemList(BaseModel):
    items: List[shortItem]

class Item(BaseModel):
    description: str
    searchid: int
    url: str
    image: str
    message: str
    itemsearch: str
    listedprice: float
    estimateprice: float
    minprice: float
    maxprice: float

class ItemList(BaseModel):
    items: List[ItemCreate]
    
@app.post("/rank")
async def rank(item_list: shortItemList):
    # Extract the URLs from the items
    item_urls = [item.url for item in item_list.items]

    return {"urls": item_urls}


@app.post("/viable")
async def viable(item: ItemCreate):
    try:
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice
        """
        result = await conn.fetchrow(query, item.description, item.searchid, item.url, item.image, item.message, item.itemsearch, item.listedprice, item.estimateprice, item.minprice, item.maxprice)
        await app.state.db_pool.release(conn)
        return {
            "id": result["id"],
            "description": result["description"],
            "searchid": result["searchid"],
            "url": result["url"],
            "image": result["image"],
            "message": result["message"],
            "itemsearch": result["itemsearch"],
            "listedprice": result["listedprice"],
            "estimateprice": result["estimateprice"],
            "minprice": result["minprice"],
            "maxprice": result["maxprice"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {e}")

@app.post("/viables")
async def viables(item_list: ItemList):
    try:
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice
        """
        for item in item_list.items:
            
            result = await conn.fetchrow(query, item.description, item.searchid, item.url, item.image, item.message, item.itemsearch, item.listedprice, item.estimateprice, item.minprice, item.maxprice)
        await app.state.db_pool.release(conn)
        return "Added viable options"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {e}")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
