# main.py
import os
import json
import logging
import io
import wave
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn
import speech_recognition as sr
from PIL import Image
import pytesseract

# Set the Tesseract command path explicitly (fallback if not in PATH)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Import your database functions and error handlers
from database import create_db, insert_ticket, get_all_tickets, update_ticket, get_team_performance, get_agent_metrics, create_conversation, add_message_to_conversation
from error_handling import handle_database_error, handle_index_error
from ai_module import handle_ticket

# Load environment variables
load_dotenv()

# Create the database if it doesn't exist
create_db()

app = FastAPI()

# CORS settings to allow your Streamlit frontend (adjust origin as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(IndexError, handle_index_error)
app.add_exception_handler(Exception, lambda req, exc: JSONResponse(
    status_code=500,
    content={"message": "Unexpected error occurred", "details": str(exc)}
))

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Customer Support Backend"}

def convert_voice_to_text(voice_bytes: bytes) -> str:
    recognizer = sr.Recognizer()
    try:
        # Write the raw audio bytes to a WAV file
        wav_audio = io.BytesIO()
        with wave.open(wav_audio, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono audio
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(16000)  # 16 kHz sample rate
            wav_file.writeframes(voice_bytes)
        wav_audio.seek(0)

        with sr.AudioFile(wav_audio) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError as e:
        return f"Speech recognition service error: {e}"
    except Exception as e:
        return f"Error processing audio: {e}"

# Function to extract text from an image
def extract_text_from_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text.strip()
    except Exception as e:
        logging.error(f"Error extracting text from image: {e}")
        return ""

@app.post("/submit_ticket/")
async def submit_ticket(
    customer_name: str = Form(...),
    issue_text: Optional[str] = Form(None),
    voice: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None)
):
    try:
        if voice:
            voice_bytes = await voice.read()
            issue_text = convert_voice_to_text(voice_bytes)
        elif image:
            image_bytes = await image.read()
            issue_text = extract_text_from_image(image_bytes)

        if not issue_text:
            raise HTTPException(status_code=400, detail="No valid input provided")

        # Process with AI and get response
        ai_response = await handle_ticket(issue_text)
        
        # Store ticket in database with AI response
        ticket_id = insert_ticket(customer_name, issue_text, ai_response)
        
        if safe_get(ai_response, "recommendation", {}).get("confidence", 0) >= 95:
            return {"message": "Resolved instantly", "AI Response": ai_response, "ticket_id": ticket_id}
        else:
            return {"message": "Ticket submitted for further review", "AI Response": ai_response, "ticket_id": ticket_id}
    except Exception as e:
        logging.exception("Error in submit_ticket:")
        raise HTTPException(status_code=500, detail=f"Error submitting ticket: {str(e)}")

# Sort tickets by newest first and sync with user dashboard
@app.get("/get_tickets/", response_model=List[dict])
def get_tickets(query: Optional[str] = None):
    try:
        tickets = get_all_tickets()
        if query:
            tickets = [t for t in tickets if query.lower() in t['issue_text'].lower()]
        
        # Ensure all required fields are present
        return [{
            "id": ticket['id'],
            "customer_name": ticket['customer_name'],
            "issue_text": ticket['issue_text'],
            "summary": ticket['summary'],
            "resolution": ticket['resolution'],
            "status": ticket['status'],
            "ai_response": ticket.get('ai_response'),
            "created_at": ticket['created_at']
        } for ticket in tickets]
    except Exception as e:
        logging.exception("Error in get_tickets:")
        raise HTTPException(status_code=500, detail=f"Error fetching tickets: {str(e)}")

@app.post("/process_ticket/")
def process_ticket(ticket_id: int, issue_text: str):
    try:
        ai_response = handle_ticket(issue_text)
        update_ticket(ticket_id, ai_response.get("summary", ""), ai_response.get("recommendation", {}).get("solution", ""), ai_response.get("estimated_time", ""))
        return {"message": "Ticket processed successfully", "AI Response": ai_response}
    except Exception as e:
        logging.exception("Error processing ticket:")
        raise HTTPException(status_code=500, detail=f"Error processing ticket: {str(e)}")

@app.post("/chat/")
async def chat_endpoint(request: Request):
    try:
        # Log the raw incoming request data
        raw_body = await request.body()
        logging.debug(f"Raw request body: {raw_body}")

        # Parse the JSON data
        data = await request.json()
        logging.debug(f"Parsed JSON data: {data}")

        # Extract message and customer_name
        message = data.get("message", "")
        customer_name = data.get("customer_name", "")

        if not message or not customer_name:
            logging.error("Missing required fields: message or customer_name")
            return JSONResponse(content={"error": "Missing required fields"}, status_code=400)

        # Process the message using AI agents
        response = await handle_ticket(message)
        logging.debug(f"AI Response: {response}")

        return JSONResponse(content=response, status_code=200)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e}")
        return JSONResponse(content={"error": "Invalid JSON format"}, status_code=400)
    except Exception as e:
        logging.exception("Error in /chat/ endpoint")
        return JSONResponse(content={"error": "Internal server error", "details": str(e)}, status_code=500)

def format_response(raw: dict) -> str:
    parts = []
    if raw.get("summary", {}).get("text"):
        parts.append(f"📝 Summary: {raw['summary']['text']}")
    if raw.get("actions"):
        parts.append("🔧 Recommended Actions:")
        parts.extend([f"- {a['description']}" for a in raw["actions"]])
    if raw.get("recommendation", {}).get("solution"):
        parts.append(f"✅ Solution: {raw['recommendation']['solution']} (Confidence: {raw['recommendation'].get('confidence', 0)}%)")
    return "\n".join(parts) if parts else "I'm still learning how to help with that. Please try rephrasing."

def handle_image(image_bytes: bytes) -> str:
    return "I've received your image and I'm processing it."

def safe_get(data, key, default=None):
    if not data:
        return default
    if isinstance(data, dict):
        return data.get(key, default)
    return default

@app.get("/admin/metrics")
async def get_admin_metrics():
    try:
        tickets = get_all_tickets()
        resolved_tickets = len([t for t in tickets if t[5] == 'Resolved'])
        unresolved_tickets = len(tickets) - resolved_tickets

        return {
            "active_tickets": unresolved_tickets,
            "resolved_tickets": resolved_tickets,
            "timeline": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "resolution_rate": calculate_resolution_rate(tickets),
            "satisfaction": [4.2, 4.3, 4.4, 4.3, 4.5],
            "overall_resolution_rate": 90,
            "avg_response_time": 15
        }
    except Exception as e:
        logging.exception("Error in admin metrics:")
        raise HTTPException(status_code=500, detail=str(e))

def calculate_resolution_rate(tickets):
    resolved = len([t for t in tickets if t[4] == 'Resolved'])
    total = len(tickets) if tickets else 1
    return round((resolved / total) * 100, 2)

# Fix Team Management tab
@app.get("/admin/teams", response_model=List[dict])
async def get_teams():
    try:
        teams = get_team_performance()
        return [
            {
                "id": team[0],
                "name": team[1],
                "specialty": team[2],
                "availability": bool(team[3]),
                "performance_score": team[4],
                "total_tickets": team[5],
                "resolution_rate": team[6]
            }
            for team in teams
        ]
    except Exception as e:
        logging.exception("Error fetching teams:")
        raise HTTPException(status_code=500, detail="Error fetching team data")

# Fix Agent Metrics tab
@app.get("/admin/agent-metrics", response_model=List[dict])
def get_agent_metrics_endpoint():
    try:
        metrics = get_agent_metrics()
        return metrics if metrics else []
    except Exception as e:
        logging.exception("Error fetching agent metrics:")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")

@app.get("/suggestions")
def get_suggestions():
    try:
        tickets = get_all_tickets()
        return {
            "suggestions": [
                {
                    "ticket_id": t[0],
                    "customer_name": t[1],
                    "suggestion": generate_suggestion(t)
                }
                for t in tickets if t[4] == 'Pending'
            ]
        }
    except Exception as e:
        logging.exception("Suggestions error:")
        raise HTTPException(status_code=500, detail="Error generating suggestions")
    except IndexError:
        raise HTTPException(status_code=500, detail="Data format mismatch in tickets")

def generate_suggestion(ticket):
    if "technical" in ticket[2].lower():
        return "Escalate to technical team"
    return "Assign to general support"

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled error:")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
