import logging
import os
import json
from google.cloud import secretmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from dotenv import load_dotenv

from agent import PicSeeAgent

load_dotenv()

logging.basicConfig(level=logging.INFO) # Set base logging level to INFO
logging.getLogger('google_genai').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

logger.info("Starting FastAPI application setup...")

app = FastAPI()
logger.info("FastAPI app instance created.")

picsee_agent = PicSeeAgent()
logger.info("PicSeeAgent instance created.")

templates = Jinja2Templates(directory="templates")
logger.info("Jinja2Templates configured.")

# Cache for valid employee IDs
VALID_EMPLOYEE_IDS = []
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "awsomecathay") # Use project_id from environment variable or default
SECRET_ID = "VALID_EMPLOYEE_IDS"
SECRET_NAME = f"projects/{PROJECT_ID}/secrets/{SECRET_ID}/versions/latest"

# Secret Manager client will be initialized only when needed
_secret_manager_client = None

async def get_valid_employee_ids():
    """Fetches the list of valid employee IDs from Google Secret Manager or local environment variable."""
    global VALID_EMPLOYEE_IDS, _secret_manager_client

    if VALID_EMPLOYEE_IDS: # Already loaded
        return VALID_EMPLOYEE_IDS

    local_ids_str = os.getenv("LOCAL_VALID_EMPLOYEE_IDS")
    if local_ids_str:
        try:
            VALID_EMPLOYEE_IDS = json.loads(local_ids_str)
            logging.info(f"Successfully loaded {len(VALID_EMPLOYEE_IDS)} valid employee IDs from local environment variable.")
            return VALID_EMPLOYEE_IDS
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding LOCAL_VALID_EMPLOYEE_IDS from .env: {e}")
            raise HTTPException(status_code=500, detail="Invalid format for local employee IDs.")

    # If not loaded from local env, try Secret Manager
    if _secret_manager_client is None:
        try:
            _secret_manager_client = secretmanager.SecretManagerServiceClient()
        except Exception as e:
            logging.error(f"Failed to initialize SecretManagerServiceClient: {e}")
            raise HTTPException(status_code=500, detail="Could not initialize Secret Manager client.")

    try:
        response = _secret_manager_client.access_secret_version(name=SECRET_NAME)
        payload = response.payload.data.decode("UTF-8")
        VALID_EMPLOYEE_IDS = json.loads(payload)
        logging.info(f"Successfully loaded {len(VALID_EMPLOYEE_IDS)} valid employee IDs from Secret Manager.")
    except Exception as e:
        logging.error(f"Error accessing Secret Manager secret {SECRET_NAME}: {e}")
        raise HTTPException(status_code=500, detail="Could not load employee ID validation data.")

    return VALID_EMPLOYEE_IDS

async def verify_employee_id(
    employee_id: str = Header(..., alias="X-Employee-ID"),
    valid_ids: list[str] = Depends(get_valid_employee_ids)
):
    """Dependency to verify the employee ID from the X-Employee-ID header."""
    if employee_id not in valid_ids:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Employee ID.")
    return employee_id

class Message(BaseModel):
    role: str
    content: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

class ChatRequest(BaseModel):
    messages: list[Message]

@app.post("/chat")
async def chat(request: ChatRequest, current_employee_id: str = Depends(verify_employee_id)): # Add dependency
    response = await picsee_agent.process_message(request.messages)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
