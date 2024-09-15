import os
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, ValidationError
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from together import Together
from typing import List
from Prompts.BrowsingAgent import RANK_PROMPT_TEMPLATE
from Prompts.NegotiationAgent import NEGOTIATION_PROMPT_TEMPLATE
from Prompts.ValidateAgent import VALIDATE_PROMPT_TEMPLATE
import json
import json
import re
import logging

logging.basicConfig(filename='negotiation.log',
                    level=logging.INFO,
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


class ValidateItem(BaseModel):
    description: str
    price: float
    listedprice: float
    message: str
    datepublished: str
    url: str


class ValidateRequest(BaseModel):
    request: str
    items: List[ValidateItem]


class ValidatedItem(BaseModel):
    item_id: str
    reasoning: str
    relevant: int
    first_message: str


class ValidateResponse(BaseModel):
    validated_items: List[ValidatedItem]


class ChatRequest(BaseModel):
    message: str
    chat_history: list = []


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    context: str
    users_goal: str
    messages: List[Message]


class NegotiationResponse(BaseModel):
    reasoning: str
    content: str


class ChatResponse(BaseModel):
    response: NegotiationResponse
    conversation_ended: bool


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
        raise HTTPException(status_code=500,
                            detail=f"Database connection failed: {e}")


@app.post("/rank")
async def rank_endpoint(request: Request):
    try:
        # Parse request JSON
        request_json = await request.json()
        print("Parsed request:", request_json)

        # Create listings text
        listings_text = "\n\n".join([
            f"Item description: {item.get('description', 'N/A')}\n"
            f"Price: {item.get('price', 'N/A')}\n"
            f"url: {item.get('url', 'N/A')}"
            for item in request_json.get("items", [])
        ])
        print("Listings text:", listings_text)

        rank_prompt = RANK_PROMPT_TEMPLATE.format(request=request_json.get(
            "request", ""),
                                                  listings=listings_text)
        messages = [{"role": "user", "content": rank_prompt}]
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=messages,
            max_tokens=1024,
            temperature=0,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
        )
        rank_response = completion.choices[0].message.content
        print("Raw AI response:", rank_response)

        # Attempt to clean the response if it's not a valid JSON
        cleaned_response = rank_response.strip()
        if not (cleaned_response.startswith('[')
                and cleaned_response.endswith(']')):
            cleaned_response = cleaned_response.split('[',
                                                      1)[-1].rsplit(']', 1)[0]
            cleaned_response = f"[{cleaned_response}]"
        print("Cleaned response:", cleaned_response)

        parsed_response = json.loads(cleaned_response)
        print("Parsed response:", parsed_response)

        # Extract the URLs
        url_list = [item['url'] for item in parsed_response]
        # Ensure the response is in the correct format
        return url_list
        # top_listings = [Listing(**url) for url in parsed_response]
        # if rank_response.strip().lower() == "null" or rank_response.strip(
        # ) == "[]":
        #     return BrowsingResponse(top_listings=None)
        # return BrowsingResponse(top_listings=top_listings)
    
    except json.JSONDecodeError as json_error:
        print(f"JSON Decode Error: {str(json_error)}")
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON response from AI: {str(json_error)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Create new item in the database
@app.post("/searchItems")
async def search_item(request: Request):
    try:
        # print(item)
        item = await request.json()
        print("Parsed request:", item)
        # item = json.loads(parsed)

        # Create listings text
        # listings_text = "\n\n".join([
        #     f"userid: {item.get('userid', 'N/A')}\n"
        #     f"searchitem: {item.get('searchitem', 'N/A')}\n"
        #     f"minprice: {item.get('minprice', 'N/A')}\n",
        #     f"maxprice: {item.get('maxprice', 'N/A')}"
        #     for item in request_json.get("items", [])
        # ])
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item_search (userid, searchitem, minprice, maxprice)
            VALUES ($1, $2, $3, $4)
            RETURNING id, userid, searchitem, minprice, maxprice
        """
        result = await conn.fetchrow(query, item['userid'], item['searchitem'],
                                     item['minprice'], item['maxprice'])
        await app.state.db_pool.release(conn)
        return {
            "id": result["id"],
            "userid": result["userid"],
            "searchitem": result["searchitem"],
            "minprice": result["minprice"],
            "maxprice": result["maxprice"]
        }
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to create item: {e}")


@app.post("/addItem")
async def create_item(request: Request):
    try:
        item = await request.json()
        print("Parsed request:", item)
        
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished))
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished
        """
        result = await conn.fetchrow(query, item['description'], item['searchid'],
                                     item['url'], item['image'], item['message'],
                                     item['itemsearch'], item['listedprice'],
                                     item['estimateprice'], item['minprice'],
                                     item['maxprice'], item['datepublished'])
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
        raise HTTPException(status_code=500,
                            detail=f"Failed to create item: {e}")


class ItemList(BaseModel):
    items: List[Item]


# @app.post("/rank")
# async def rank(item_list: shortItemList):
#     # Extract the URLs from the items
#     item_urls = [item.url for item in item_list.items]

#     return {"urls": item_urls}


@app.post("/viable")
async def viable(item: Item):
    try:
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished
        """
        result = await conn.fetchrow(query, item['description'], item['searchid'],
             item['url'], item['image'], item['message'],
             item['itemsearch'], item['listedprice'],
             item['estimateprice'], item['minprice'],
             item['maxprice'], item['datepublished'])
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
        raise HTTPException(status_code=500,
                            detail=f"Failed to create item: {e}")


@app.post("/viables")
async def viables(request: Request):
    try:
        request_json = await request.json()
        # print("Parsed request:", request_json)
        conn = await app.state.db_pool.acquire()
        query = """
            INSERT INTO item (description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id, description, searchid, url, image, message, itemsearch, listedprice, estimateprice, minprice, maxprice, datepublished
        """
        for item in request_json.get("items", []):

            result = await conn.fetchrow(query, item.get('description', 'N/A'), item.get('searchid', 'N/A'),
                 item.get('url', 'N/A'), item.get('image', 'N/A'), item.get('message', 'N/A'),
                 item.get('itemsearch', 'N/A'), item.get('listedprice', 'N/A'),
                 item.get('estimateprice', 'N/A'), item.get('minprice', 'N/A'),
                 item.get('maxprice', 'N/A'), item.get('datepublished', 'N/A'))
        await app.state.db_pool.release(conn)
        return "Added viable options"
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to create item: {e}")


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


@app.post("/validate", response_model=ValidateResponse)
async def validate_endpoint(request: ValidateRequest):
    try:
        listings_text = "\n\n".join([
            f"Item description: {item.description}\n"
            f"Price: {item.price}\n"
            f"Listed price: {item.listedprice}\n"
            f"Message: {item.message}\n"
            f"Date published: {item.datepublished}\n"
            f"URL: {item.url}" for item in request.items
        ])

        validate_prompt = VALIDATE_PROMPT_TEMPLATE.format(
            request=request.request, listings=listings_text)

        messages = [{"role": "user", "content": validate_prompt}]

        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=messages,
            max_tokens=1024,
            temperature=0,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
        )

        validate_response = completion.choices[0].message.content

        # Parse the response
        parsed_response = json.loads(validate_response)

        # Convert the parsed response to ValidatedItem objects
        validated_items = [ValidatedItem(**item) for item in parsed_response]

        return ValidateResponse(validated_items=validated_items)

    except json.JSONDecodeError as json_error:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON response from LLM: {str(json_error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Construct the conversation history
        conversation_history = "\n".join(
            [f"{msg.role}: {msg.content}" for msg in request.messages])

        negotiation_prompt = NEGOTIATION_PROMPT_TEMPLATE.format(
            context=request.context,
            users_goal=request.users_goal,
            conversation_history=conversation_history)

        messages = [{"role": "user", "content": negotiation_prompt}]

        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1,
        )

        bot_response = completion.choices[0].message.content
        logging.info(f"AI Response: {bot_response}")

        # Parse the JSON response
        negotiation_response = json.loads(bot_response)

        # Check if this is an ending message
        conversation_ended = is_ending_message(negotiation_response['content'])

        return ChatResponse(
            response=NegotiationResponse(**negotiation_response),
            conversation_ended=conversation_ended)

    except json.JSONDecodeError as json_error:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON response from bot: {str(json_error)}")
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def is_ending_message(message: str) -> bool:
    ending_patterns = [r"thank you,?\s+all the best", r"amazing,?\s+thank you"]
    return any(
        re.search(pattern, message.lower()) is not None
        for pattern in ending_patterns)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
