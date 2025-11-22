import os
import json
import requests
from pydantic import BaseModel, Field

# 1. Define the Structure (Pydantic used for validation after receiving JSON)
class EnsoParams(BaseModel):
    color_hex: str = Field(description="The hex color of the ink, e.g., #FF0000")
    complexity: int = Field(description="Number of brush strokes (20-100)")
    chaos: float = Field(description="How messy/wobbly the circle is (0.1-2.0)")
    text_overlay: str = Field(description="A short, cryptic loading message (e.g., 'ENTERING VOID')")

def get_enso_params_from_prompt(prompt: str, api_key: str, model: str = "gpt-4o-2024-08-06", base_url: str | None = None) -> EnsoParams:
    """
    Uses requests to call the LLM Provider (Requesty/OpenAI-compatible) and translate a vibe.
    base_url can be a full base like 'https://router.requesty.ai/v1' or the full endpoint
    'https://router.requesty.ai/v1/chat/completions'. If None, falls back to env LLM_BASE_URL
    or the Requesty default.
    """
    if not api_key:
        print("⚠️ No API Key provided.")
        return EnsoParams(color_hex="#FF0000", complexity=50, chaos=1.5, text_overlay="NO KEY")

    print(f"🧠 Director ({model}) thinking about: '{prompt}'...")
    
    # JSON Schema for Structured Outputs
    json_schema = {
        "name": "enso_params",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "color_hex": {"type": "string", "description": "Hex color e.g. #FF0000"},
                "complexity": {"type": "integer", "description": "Number of brush strokes (20-100)"},
                "chaos": {"type": "number", "description": "Chaos factor (0.1-2.0)"},
                "text_overlay": {"type": "string", "description": "Cryptic loading message"}
            },
            "required": ["color_hex", "complexity", "chaos", "text_overlay"],
            "additionalProperties": False
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Add Requesty-specific headers if needed, e.g. HTTP-Referer
        "HTTP-Referer": "https://github.com/mojomast/designussy", 
        "X-Title": "Unwritten Worlds"
    }

    # Resolve endpoint (Requesty default). Compose /chat/completions if needed.
    base = (base_url or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")).rstrip('/')
    url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    
    payload = {
        "model": model, 
        "messages": [
             {"role": "system", "content": "You are the Art Director for 'Unwritten Worlds'. Translate user moods into JSON parameters for the Ink Enso generator."},
             {"role": "user", "content": f"Generate parameters for this mood: {prompt}"}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": json_schema
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        params_dict = json.loads(content)
        return EnsoParams(**params_dict)
        
    except Exception as e:
        print(f"❌ Director Error: {e}")
        return EnsoParams(color_hex="#000000", complexity=30, chaos=0.5, text_overlay="ERROR")