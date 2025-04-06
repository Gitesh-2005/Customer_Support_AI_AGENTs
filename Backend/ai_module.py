# ai_module.py
import os
import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

class AIAgent:
    def __init__(self, name: str, prompt_template: str, model: str = "llama-3.3-70b-versatile"):
        self.name = name
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.prompt_template = prompt_template

    async def process(self, content: str, context: str = "") -> Dict[str, Any]:
        try:
            # Format messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": self.prompt_template + "\nImportant: Always respond with valid JSON format and provide contextually relevant responses."
                },
                {
                    "role": "user",
                    "content": f"Content: {content}\nContext: {context}"
                }
            ]

            # Make the API call
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,  # Adjusted for more creative responses
                max_tokens=2048,
                top_p=0.9,
                stream=False
            )

            # Log rate-limit and response headers (if available)
            headers = getattr(completion, "headers", {})
            logging.debug("API Response Headers: %s", headers)

            if not completion.choices:
                raise ValueError("No response from AI API")

            response_text = completion.choices[0].message.content.strip()
            logging.debug("Raw AI Response Text: %s", response_text)

            # Parse the response as JSON
            response_data = json.loads(response_text)
            if isinstance(response_data, str):
                response_data = json.loads(response_data)
            if not isinstance(response_data, dict):
                raise ValueError("Response is not a JSON object")
            return response_data

        except json.JSONDecodeError as e:
            logging.error("JSON parsing error in %s: %s. Response: %s", self.name, str(e), response_text)
            return {
                "error": "Invalid JSON response format",
                "original_response": response_text,
                "details": str(e)
            }
        except Exception as e:
            logging.exception("Error in %s:", self.name)
            return {
                "error": "Processing error",
                "details": str(e),
                "suggestion": "Please retry with a different query"
            }

class MultiAgentSystem:
    def __init__(self):
        self.agents = {
            "summarizer": AIAgent(
                "Summarization Agent",
                prompt_template="""Analyze the customer support conversation and generate a concise summary in JSON format.
Check for specific issues like login problems, technical issues, or account-related problems before categorizing as a greeting.
If the message contains any problem description, it should not be categorized as a greeting.

{
    "summary": "Brief description of the specific issue",
    "metadata": {
        "sentiment": "Analyze user sentiment (positive/negative/neutral)",
        "priority": "Determine priority based on issue severity (high/medium/low)",
        "category": "Categorize issue (login issue/technical/account/etc.)",
        "conversation_id": "Generate unique ID"
    }
}"""),
            "action_extractor": AIAgent(
                "Action Extraction Agent",
                prompt_template="""Identify specific actions needed to resolve the issue and return them in JSON format:
{
    "actions": [
        {
            "type": "Action type (Authentication/Password Reset/Account Recovery/Technical Fix)",
            "description": "Detailed steps to resolve the specific issue",
            "priority": "Priority level (Critical/High/Medium/Low)"
        }
    ]
}"""),
            "resolver": AIAgent(
                "Resolution Recommendation Agent",
                prompt_template="""Recommend specific solutions based on the identified issue. Return the result in JSON format:
{
    "recommendation": {
        "solution": "Specific solution to the identified problem",
        "confidence": "Confidence level",
        "steps": ["Step-by-step resolution steps"],
        "resources": ["Relevant documentation/guides"]
    },
    "similar_cases": ["Related ticket IDs"]
}"""
            ),
        }

    def extract_structured_data(self, text: str) -> Dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logging.error("JSON parsing error: %s. Text: %s", str(e), text)
            return {}

# Initialize the multi-agent system
agent_system = MultiAgentSystem()

import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List

def safe_parse(data, default):
    """Parse data as JSON if it's a string; otherwise, return data or default."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return default
    elif isinstance(data, dict):
        return data
    return default

def safe_get(data, key, default=None):
    """Safely get a value from a dictionary."""
    return data.get(key, default) if isinstance(data, dict) else default

async def handle_ticket(issue_text: str, context: list = None) -> dict:
    """
    Process a ticket using the multi-agent system with enhanced error handling.
    Ensures the final "summary" field is always a dictionary with a "text" key.
    """
    # Default response structure.
    ai_response = {
        "summary": {"text": "", "category": "general"},
        "metadata": {"sentiment": "neutral", "priority": "low", "category": "general inquiry", "conversation_id": None},
        "actions": [],
        "recommendation": {"solution": "", "confidence": 0},
        "similar_cases": []
    }

    # Simple greeting shortcut.
    if "hello" in issue_text.lower() or "hi" in issue_text.lower():
        return {
            "summary": {"text": "Customer greeting received"},
            "metadata": {
                "sentiment": "positive",
                "priority": "low",
                "category": "greeting",
                "conversation_id": f"conv_{uuid.uuid4().hex[:8]}"
            },
            "actions": [{
                "type": "GreetingResponse",
                "description": "Provide welcome message",
                "priority": "high"
            }],
            "recommendation": {
                "solution": "Welcome to support! How can I help you today?",
                "confidence": 95,
                "steps": ["Ask user to describe their issue"],
                "resources": []
            },
            "similar_cases": []
        }

    try:
        logging.debug("Calling summarizer agent")
        summary = safe_parse(await agent_system.agents["summarizer"].process(issue_text, context) or {}, {"summary": "", "metadata": {}})

        logging.debug("Calling action_extractor agent")
        actions = safe_parse(await agent_system.agents["action_extractor"].process(issue_text, context) or {}, {"actions": []})

        logging.debug("Calling resolver agent")
        resolution = safe_parse(await agent_system.agents["resolver"].process(issue_text, context) or {}, {"recommendation": {}, "similar_cases": []})

        logging.debug("Raw summary response: %s", summary)
        logging.debug("Raw actions response: %s", actions)
        logging.debug("Raw resolution response: %s", resolution)

        # Ensure responses are dictionaries.
        if not isinstance(summary, dict):
            summary = {"summary": str(summary), "metadata": {}}
        if not isinstance(actions, dict):
            actions = {"actions": []}
        if not isinstance(resolution, dict):
            resolution = {"recommendation": {}, "similar_cases": []}

        # Process recommendation.
        raw_reco = safe_parse(resolution.get("recommendation", {}), {"solution": "", "confidence": "0"})
        confidence_value = raw_reco.get("confidence", "0")
        try:
            if isinstance(confidence_value, str):
                if confidence_value.lower() in ["high", "medium", "low"]:
                    confidence_numeric = {"high": 80, "medium": 50, "low": 20}.get(confidence_value.lower(), 50)
                else:
                    confidence_numeric = int(confidence_value)
            else:
                confidence_numeric = int(confidence_value)
        except (ValueError, TypeError):
            confidence_numeric = 50

        safe_reco = {
            "solution": raw_reco.get("solution", "Default solution"),
            "confidence": confidence_numeric,
            "steps": raw_reco.get("steps", []),
            "resources": raw_reco.get("resources", [])
        }

        # Build final response.
        final_response = {
            "summary": summary.get("summary", "Issue processed"),
            "metadata": summary.get("metadata", {}),
            "actions": actions.get("actions", []),
            "recommendation": safe_reco,
            "similar_cases": resolution.get("similar_cases", [])
        }
        logging.debug("Intermediate final response: %s", final_response)

        # Ensure "summary" is always a dictionary with a "text" key.
        if not isinstance(final_response.get("summary"), dict):
            final_response["summary"] = {"text": str(final_response["summary"])}
        # Ensure "recommendation" is always a dictionary
        if not isinstance(final_response.get("recommendation"), dict):
            final_response["recommendation"] = {"solution": str(final_response["recommendation"])}
        logging.debug("Final response: %s", final_response)
        return final_response

    except Exception as e:
        logging.exception("Critical error in handle_ticket:")
        return {
            "error": "System failure",
            "details": str(e),
            "response": "I'm experiencing technical difficulties. Your issue has been logged and our team will investigate."
        }

def format_response(raw: dict) -> str:
    """
    Convert structured AI response to a user-friendly text message.
    Assumes that raw["summary"] is a dictionary with a "text" key.
    """
    parts = []
    
    summary = raw.get("summary")
    if isinstance(summary, dict):
        summary_text = summary.get("text", "") or summary.get("summary", "")
    else:
        summary_text = summary or ""
    
    if summary_text:
        parts.append(f"📝 Summary: {summary_text}")
    
    actions = raw.get("actions", [])
    if actions:
        parts.append("🔧 Recommended Actions:")
        for a in actions:
            if isinstance(a, dict):
                parts.append(f"- {a.get('description', a)}")
            else:
                parts.append(f"- {a}")
    
    recommendation = raw.get("recommendation", {})
    if isinstance(recommendation, dict):
        solution = recommendation.get("solution", "")
        confidence = recommendation.get("confidence", 0)
        if solution:
            parts.append(f"✅ Solution: {solution} (Confidence: {confidence}%)")
    elif isinstance(recommendation, str):
        parts.append(f"✅ Solution: {recommendation}")
    
    return "\n".join(parts) if parts else "I'm still learning how to help with that. Please try rephrasing."
