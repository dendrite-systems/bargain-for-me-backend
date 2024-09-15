import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ValidationError
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from together import Together
from typing import List
from Prompts.BrowsingAgent import BROWSING_PROMPT_TEMPLATE
import json
import re
import logging


logging.basicConfig(filename='negotiation.log', level=logging.INFO, 
format='%(asctime)s - %(levelname)s - %(message)s')


# Load environment variables
load_dotenv()

client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
# FastAPI app initialization
# app = FastAPI()

class ItemSearch(BaseModel):
    userid: str
    searchitem: str
    minprice: float
    maxprice: float

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
    datepublished: str

class shortItem(BaseModel):
    description: str
    imageUrl: str
    url: str
    price: float
    
class Listing(BaseModel):
    # name: str
    description: str
    price: float

class BrowsingRequest(BaseModel):
    request: str
    searchid: int
    items: List[shortItem]

class BrowsingResponse(BaseModel):
    top_listings: list[Listing]



class shortItemList(BaseModel):
    items: List[shortItem]

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

@app.post("/browse", response_model=BrowsingResponse)
async def browse_endpoint(request: BrowsingRequest):
    try:
        # for item in request.items:
            # print(item)
        listings_text = "\n\n".join([
            # f"Item name: {item.name}\n"
            f"Item description: {item.description}\n"
            f"Price: {item.price}"
            for item in request.items
        ])

        updated_prompt = BROWSING_PROMPT_TEMPLATE.format(
            request=request.request,
            listings=listings_text
        )

        messages = [{"role": "user", "content": updated_prompt}]

        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=messages,
            max_tokens=1024,
            temperature=0,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
        )

        ai_response = completion.choices[0].message.content

        # Attempt to clean the response if it's not a valid JSON
        cleaned_response = ai_response.strip()
        if not (cleaned_response.startswith('[') and cleaned_response.endswith(']')):
            cleaned_response = cleaned_response.split('[', 1)[-1].rsplit(']', 1)[0]
            cleaned_response = f"[{cleaned_response}]"

        parsed_response = json.loads(cleaned_response)
        print(parsed_response)
        # Ensure the response is in the correct format
        top_listings = [Listing(**item) for item in parsed_response]

        return BrowsingResponse(top_listings=top_listings)

    except json.JSONDecodeError as json_error:
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from AI: {str(json_error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/browse2", response_model=BrowsingResponse)
async def browse2_endpoint(request: BrowsingRequest):
    try:
        # for item in request.items:
            # print(item)
        listings_text = "\n\n".join([
            # f"Item name: {item.name}\n"
            f"Item description: {item.description}\n"
            f"Price: {item.price}"
            for item in request.items
        ])

        updated_prompt = BROWSING_PROMPT_TEMPLATE.format(
            request=request.request,
            listings=listings_text
        )

        messages = [{"role": "user", "content": updated_prompt}]

        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=messages,
            max_tokens=1024,
            temperature=0,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
        )

        ai_response = completion.choices[0].message.content

        # Attempt to clean the response if it's not a valid JSON
        cleaned_response = ai_response.strip()
        if not (cleaned_response.startswith('[') and cleaned_response.endswith(']')):
            cleaned_response = cleaned_response.split('[', 1)[-1].rsplit(']', 1)[0]
            cleaned_response = f"[{cleaned_response}]"

        parsed_response = json.loads(cleaned_response)
        print(parsed_response)
        # Ensure the response is in the correct format
        top_listings = [Listing(**item) for item in parsed_response]

        return BrowsingResponse(top_listings=top_listings)

    except json.JSONDecodeError as json_error:
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from AI: {str(json_error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
async def create_item(item: Item):
    try:
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished))
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished
        """
        result = await conn.fetchrow(query, item.description, item.searchid, item.url, item.image, item.message, item.itemsearch, item.listedprice, item.estimateprice, item.minprice, item.maxprice, item.datepublished)
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
            "maxprice": result["maxprice"],
            "datepublished": result["datepublished"]
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


class ItemList(BaseModel):
    items: List[Item]
    
@app.post("/rank")
async def rank(item_list: shortItemList):
    # Extract the URLs from the items
    item_urls = [item.url for item in item_list.items]

    return {"urls": item_urls}


@app.post("/viable")
async def viable(item: Item):
    try:
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished
        """
        result = await conn.fetchrow(query, item.description, item.searchid, item.url, item.image, item.message, item.itemsearch, item.listedprice, item.estimateprice, item.minprice, item.maxprice, item.datepublished)
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
            "maxprice": result["maxprice"],
            "datepublished": result["datepublished"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {e}")

@app.post("/viables")
async def viables(item_list: ItemList):
    try:
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished
        """
        for item in item_list.items:
            
            result = await conn.fetchrow(query, item.description, item.searchid, item.url, item.image, item.message, item.itemsearch, item.listedprice, item.estimateprice, item.minprice, item.maxprice, item.datepublished)
        await app.state.db_pool.release(conn)
        return "Added viable options"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {e}")

@app.get("/viables")
async def getViables(id: int = Query(...)):
    try:
        conn = await app.state.db_pool.acquire()
        query = "SELECT * FROM item WHERE searchid = $1"
        params = id
        items = await conn.fetch(query, params)

        if not items:
            raise HTTPException(status_code=404, detail="Item not found")

        return items

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Ensure the connection is released back to the pool
        if conn:
            await app.state.db_pool.release(conn)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
