import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from together import Together
from dotenv import load_dotenv
import json
import asyncpg
from Prompts.NegotiatorAgent import PROMPT_TEMPLATE

app = FastAPI()
# local run
# load_dotenv()
# client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

load_dotenv()
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.sql import text
from typing import List
from pydantic import BaseModel

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()

# replit run
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
print(os.getenv("TOGETHER_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    chat_history: list = []
    seller_response: dict = {}

class ChatResponse(BaseModel):
    message: str
    offer: float | None = None

class ItemCreate(BaseModel):
    name: str
    description: str


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        updated_prompt = PROMPT_TEMPLATE.format(
            request=request.message,
            seller_response=json.dumps(request.seller_response)
        )
        
        messages = request.chat_history + [{"role": "user", "content": updated_prompt}]
        
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=messages,
            max_tokens=1024,
            temperature=0,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
        )
        
        ai_response = json.loads(completion.choices[0].message.content)
        return ChatResponse(**ai_response)
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON response from AI")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/items", response_model=dict)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    print(item.name, item.description)
    query = text("INSERT INTO items (name, description) VALUES (:name, :description) RETURNING id, name, description")
    result = await db.execute(query, {"name": item.name, "description": item.description})
    await db.commit()
    new_item = result.first()
    return {"id": new_item.id, "name": new_item.name, "description": new_item.description}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)