import os
from groq import Groq
from typing import Dict, Any, List
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIAgent:
    def __init__(self, name: str, prompt_template: str, model: str = "llama-3.3-70b-versatile"):
        self.name = name
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.prompt_template = prompt_template

    def process(self, content: str, context: str = "") -> Dict[str, Any]:
        try:
            # Format messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": self.prompt_template + "\nImportant: Always respond with valid JSON format."
                },
                {
                    "role": "user",
                    "content": f"Content: {content}\nContext: {context}"
                }
            ]

            # Make API call with proper error handling
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"},  # Enforce JSON output
                max_tokens=2048,
                top_p=0.9,
                stream=False
            )

            if not completion.choices:
                raise ValueError("No response from Groq API")

            response_text = completion.choices[0].message.content.strip()
            print(" Response: ,",response_text)  # Log the raw response

            # Parse the response as JSON
            response_data = json.loads(response_text)
            if not isinstance(response_data, dict):
                raise ValueError("Response is not a JSON object")
            return response_data

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}\nResponse: {response_text}")
            return {
                "error": "Invalid JSON response format",
                "original_response": response_text,
                "details": str(e)
            }
        except Exception as e:
            print(f"Error in {self.name}: {str(e)}")
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
                prompt_template="""Analyze the customer support conversation and generate a concise summary in JSON format:
                {
                    "summary": "Brief summary of the issue",
                    "metadata": {
                        "sentiment": "Sentiment analysis result",
                        "priority": "Priority level",
                        "category": "Issue category",
                        "conversation_id": "Unique conversation ID"
                    }
                }"""
            ),
            "action_extractor": AIAgent(
                "Action Extraction Agent",
                prompt_template="""Identify all actionable tasks in the conversation and return them in JSON format:
                {
                    "actions": [
                        {
                            "type": "Action type (e.g., Technical fix, Refund, Escalation)",
                            "description": "Specific steps required",
                            "priority": "Priority level (Critical/High/Medium)"
                        }
                    ]
                }"""
            ),
            "router": AIAgent(
                "Task Routing Agent",
                prompt_template="""Route tasks to teams based on issue type, urgency, and resources. Return the result in JSON format:
                {
                    "task": "Task description",
                    "route_to": "Team name",
                    "reason": "Reason for routing"
                }"""
            ),
            "resolver": AIAgent(
                "Resolution Recommendation Agent",
                prompt_template="""Recommend solutions using past tickets and knowledge base articles. Return the result in JSON format:
                {
                    "recommendation": "Suggested fix",
                    "confidence": "Confidence level",
                    "similar_cases": ["List of similar ticket IDs"]
                }"""
            ),
            "time_estimator": AIAgent(
                "Resolution Time Estimation Agent",
                prompt_template="""Predict resolution time and return the result in JSON format:
                {
                    "estimate": "Estimated time for resolution",
                    "confidence": "Confidence level"
                }"""
            ),
            "feedback_learner": AIAgent(
                "Feedback Learning Agent",
                prompt_template="""Analyze resolved tickets and provide insights in JSON format:
                {
                    "insights": [
                        {
                            "description": "Insight description",
                            "impact": "Impact of the insight"
                        }
                    ]
                }"""
            ),
            "supervisor": AIAgent(
                "Supervisor Agent",
                prompt_template="""Orchestrate workflow and validate outputs. Return the result in JSON format:
                {
                    "workflow_status": "Status of the workflow",
                    "validation": "Validation results"
                }"""
            ),
            "sentiment_urgency": AIAgent(
                "Sentiment & Urgency Detection Agent",
                prompt_template="""Analyze text for sentiment and urgency. Return the result in JSON format:
                {
                    "sentiment": "Sentiment analysis result",
                    "urgency": "Urgency level"
                }"""
            ),
            "multimodal_support": AIAgent(
                "Multimodal Support Agent",
                prompt_template="""Process non-text inputs and return structured data in JSON format:
                {
                    "extracted_data": "Extracted information from input"
                }"""
            )
        }

    def extract_structured_data(self, text: str) -> Dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}\nText: {text}")
            return {}

# Initialize the multi-agent system
agent_system = MultiAgentSystem()

def handle_ticket(issue_text: str, context: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Process a ticket using the multi-agent system with optional context.
    """
    try:
        context_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context]) if context else "No context provided."

        # Summarize the issue
        summary_data = agent_system.agents["summarizer"].process(issue_text, context_str)

        # Extract actionable insights
        actions_data = agent_system.agents["action_extractor"].process(issue_text, context_str)

        # Recommend resolutions
        resolution_data = agent_system.agents["resolver"].process(issue_text, context_str)

        return {
            "summary": summary_data.get("summary", {}),
            "actions": actions_data.get("actions", []),
            "resolution": resolution_data.get("recommendation", {}),
            "confidence": resolution_data.get("confidence", 80)  # Default confidence
        }
    except Exception as e:
        print(f"Error processing ticket: {str(e)}")
        return {
            "error": "Error processing ticket",
            "details": str(e),
            "suggestion": "Please retry or contact support."
        }