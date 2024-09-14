import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from together import Together
from dotenv import load_dotenv
from dendrite_sdk import DendriteBrowser, DendritePage
from Prompts.NegotiatorAgent import PROMPT_TEMPLATE

app = FastAPI()
# local run
# load_dotenv()
# client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

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


@app.get("/item")
async def iten_endpoint():
    return {"name": "Chair", "description": "Comfy Blue chair", "price": 10, "URL": "https://example.com"}


@app.post("/item")
async def iten_endpoint():
    return {"name": "Chair", "description": "Comfy Blue chair", "price": 10, "URL": "https://example.com"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)