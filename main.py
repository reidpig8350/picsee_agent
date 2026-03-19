import logging
import os

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from dotenv import load_dotenv

from agent import PicSeeAgent

load_dotenv()

logging.getLogger('google_genai').setLevel(logging.ERROR)

app = FastAPI()
picsee_agent = PicSeeAgent()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

@app.post("/chat")
async def chat(request: ChatRequest):
    response = await picsee_agent.process_message(request.messages)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
