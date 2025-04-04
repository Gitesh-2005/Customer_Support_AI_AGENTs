from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from database import create_db, insert_ticket, get_all_tickets, update_ticket
from ai_module import handle_ticket
from typing import Optional
import base64
from database import create_conversation, add_message_to_conversation, get_conversation_history
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Customer Support Backend"}

@app.post("/submit_ticket/")
async def submit_ticket(
    customer_name: str = Form(...),
    issue_text: Optional[str] = Form(None),
    voice: Optional[UploadFile] = None,
    image: Optional[UploadFile] = None
):
    try:
        if voice:
            voice_bytes = await voice.read()
            issue_text = convert_voice_to_text(voice_bytes)
        elif image:
            image_bytes = await image.read()
            issue_text = handle_image(image_bytes)

        if not issue_text:
            raise HTTPException(status_code=400, detail="No valid input provided")

        insert_ticket(customer_name, issue_text)
        ai_response = handle_ticket(issue_text)

        if ai_response.get("confidence", 0) >= 95:
            return {"message": "Resolved instantly", "AI Response": ai_response}
        else:
            return {"message": "Ticket submitted for further review", "AI Response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting ticket: {str(e)}")

@app.get("/get_tickets/")
def get_tickets(query: Optional[str] = None):
    try:
        tickets = get_all_tickets()
        if query:
            tickets = [t for t in tickets if query.lower() in t[2].lower()]
        return {"tickets": [{"id": t[0], "customer_name": t[1], "issue_text": t[2], "summary": t[3], "resolution": t[4], "status": t[5], "estimated_time": t[6]} for t in tickets]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tickets: {str(e)}")

@app.post("/process_ticket/")
def process_ticket(ticket_id: int, issue_text: str):
    try:
        ai_response = handle_ticket(issue_text)
        update_ticket(ticket_id, ai_response["summary"], ai_response["resolution"], ai_response["estimated_time"])
        return {"message": "Ticket processed successfully", "AI Response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing ticket: {str(e)}")

@app.post("/proactive_prevention/")
def proactive_prevention(
    device_logs: Optional[str] = Form(None),
    network_status: Optional[str] = Form(None),
    software_status: Optional[str] = Form(None)
):
    try:
        if not device_logs or not network_status or not software_status:
            raise HTTPException(status_code=422, detail="Missing required fields")
        prevention_tips = handle_prevention(device_logs, network_status, software_status)
        return {"prevention_tips": prevention_tips}
    except Exception as e:
        print(f"Error in proactive prevention: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in proactive prevention")

@app.post("/chat/")
async def handle_chat(
    message: str = Form(None),
    customer_name: str = Form(...),
    conversation_id: Optional[int] = Form(None),
    message_history: Optional[str] = Form(None),
    image: Optional[UploadFile] = None,
    voice: Optional[UploadFile] = None,
    screenshot: Optional[str] = Form(None)
):
    try:
        # Handle the predefined initial prompt when the chatbot is opened
        if not message and not conversation_id:
            message = "Hi I need help!"
            response = "Welcome! 👋 How can I assist you today?"
            conversation_id = create_conversation(customer_name)
            add_message_to_conversation(conversation_id, message, "user")
            add_message_to_conversation(conversation_id, response, "bot")
            return {
                "response": response,
                "conversation_id": conversation_id
            }

        if not conversation_id:
            # Create a new conversation and ticket
            conversation_id = create_conversation(customer_name)
            insert_ticket(customer_name, message or "No initial message provided")

        # Process message history for context
        context = []
        if message_history:
            try:
                history = json.loads(message_history)
                context = [{"role": msg["type"], "content": msg["content"]} for msg in history]
            except json.JSONDecodeError:
                context = []

        response = ""

        if message:
            # Add user message to conversation
            add_message_to_conversation(conversation_id, message, "user")

            # Get AI response with context
            ai_response = handle_ticket(message, context=context)
            print(f"AI Response: {ai_response}")  # Log the raw response for debugging
            # Parse AI response
            if isinstance(ai_response, dict) and "summary" in ai_response:
                # Extract a concise one-liner response
                response = ai_response["summary"] #.get("brief", "I'm sorry, I couldn't process your request.")
                print(f"Parsed AI response: {response}")  # Log the parsed response
                # Include task updates if available
                if "actions" in ai_response and ai_response["actions"]:
                    response += f" | Next Steps: {', '.join(action['description'] for action in ai_response['actions'])}"

                # Include resolution if available
                if "resolution" in ai_response and ai_response["resolution"]:
                    response += f" | Resolution: {ai_response['resolution'][0].get('solution', 'No resolution provided')}"

                # Store the full AI analysis in the database
                add_message_to_conversation(conversation_id, json.dumps(ai_response), "analysis")
            else:
                # Log the issue for debugging
                print(f"Unexpected AI response format: {ai_response}")
                response = "I'm sorry, I couldn't process your request. Please try again."

        elif image:
            image_bytes = await image.read()
            response = "Image received. Analyzing..."
        elif voice:
            voice_bytes = await voice.read()
            text = convert_voice_to_text(voice_bytes)
            response = f"Voice input received: {text}"
        elif screenshot:
            response = "Screenshot received. Analyzing..."
        else:
            raise HTTPException(status_code=400, detail="No valid input provided")

        # Add AI response to the conversation
        add_message_to_conversation(conversation_id, response, "bot")

        return {
            "response": response,
            "conversation_id": conversation_id
        }
    except Exception as e:
        print(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

def format_ai_response(ai_response: dict) -> str:
    response = f"AI Analysis:\n"
    if 'summary' in ai_response and isinstance(ai_response['summary'], dict):
        response += f"Summary: {ai_response['summary'].get('brief', 'N/A')}\n"
        response += f"Severity: {ai_response['summary'].get('severity', 'N/A')}\n"
        
    if 'actions' in ai_response and isinstance(ai_response['actions'], dict):
        actions = ai_response['actions'].get('immediate_actions', [])
        if actions:
            response += "\nSuggested Actions:\n"
            response += "\n".join(f"- {action}" for action in actions)
            
    if 'resolution' in ai_response:
        response += f"\nEstimated Time: {ai_response['resolution'].get('total_estimated_time', 'Unknown')}"
    return response

# Add these helper functions
def handle_image(image_bytes: bytes) -> str:
    # Placeholder for image processing
    return "I've received your image and I'm processing it."

def convert_voice_to_text(voice_bytes: bytes) -> str:
    # Placeholder for voice-to-text conversion
    return "Voice input received."

def handle_voice_input(text: str) -> str:
    return f"I understood: {text}"

def handle_screenshot(screenshot: str) -> str:
    # Placeholder for screenshot processing
    return "I've received your screenshot and I'm analyzing it."

def handle_prevention(device_logs: str, network_status: str, software_status: str) -> str:
    # Placeholder for proactive prevention logic
    return "No issues detected. Your system is healthy."

@app.get("/admin/metrics")
async def get_admin_metrics():
    """Get performance metrics for admin dashboard"""
    try:
        return {
            "active_tickets": len([t for t in get_all_tickets() if t[5] != 'Resolved']),
            "timeline": ["Mon", "Tue", "Wed", "Thu", "Fri"],  # Replace with actual dates
            "resolution_rate": [85, 88, 87, 90, 92],  # Example data
            "satisfaction": [4.2, 4.3, 4.4, 4.3, 4.5],  # Example data
            "overall_resolution_rate": 90,
            "avg_response_time": 15
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/teams")
async def get_teams():
    """Get team information and performance"""
    try:
        teams = get_team_performance()
        return [
            {
                "id": team[0],
                "name": team[1],
                "specialty": team[2],
                "availability": team[3],
                "performance_score": team[4],
                "total_tickets": team[5],
                "resolution_rate": team[6]
            }
            for team in teams
        ]
    except Exception as e:
        print(f"Error fetching teams: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching team data")

@app.get("/admin/agent-metrics")
def get_agent_metrics():
    """Get agent performance metrics"""
    try:
        metrics = get_agent_metrics()  # Ensure this is called synchronously
        return [
            {
                "agent_id": metric[1],
                "tickets_resolved": metric[2],
                "avg_resolution_time": metric[3],
                "customer_satisfaction": metric[4],
                "efficiency_score": metric[5]
            }
            for metric in metrics
        ]
    except Exception as e:
        print(f"Error fetching agent metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching agent metrics")

@app.get("/suggestions")
def get_suggestions():
    """Provide suggestions based on database data"""
    try:
        tickets = get_all_tickets()
        suggestions = []
        for ticket in tickets:
            if ticket[5] == "Pending":
                suggestions.append({
                    "ticket_id": ticket[0],
                    "customer_name": ticket[1],
                    "issue_text": ticket[2],
                    "suggested_action": "Assign to team" if not ticket[15] else "Follow up"
                })
        return {"suggestions": suggestions}
    except Exception as e:
        print(f"Error fetching suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching suggestions")
