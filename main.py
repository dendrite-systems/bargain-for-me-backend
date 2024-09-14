import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from together import Together
from dotenv import load_dotenv
from Prompts.NegotiatorAgent import PROMPT_TEMPLATE

app = FastAPI()

load_dotenv()

client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    chat_history: list = []

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        messages = request.chat_history + [{"role": "user", 
                                            "content": PROMPT_TEMPLATE.format(request=request.message)}]
        
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            messages=messages,
            max_tokens=4096,
            temperature=0.3
        )
        return ChatResponse(response=completion.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)