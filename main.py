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

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    user_input = request.message
    response = await picsee_agent.process_message(user_input)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
