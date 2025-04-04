import os
from groq import Groq

# Load API key
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Initialize Groq client
client = Groq(api_key=api_key)

# List available models
try:
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(model)
except Exception as e:
    print(f"Error listing models: {str(e)}")
