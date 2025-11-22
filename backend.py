from fastapi import FastAPI, Query, Header, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import requests
from dotenv import load_dotenv
from generate_assets import create_void_parchment, create_ink_enso, create_sigil, create_giraffe, create_kangaroo

# Load environment variables from .env
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import the Director (Wrap in try/except in case dependencies/keys are missing)
try:
    from llm_director import get_enso_params_from_prompt
    HAS_LLM = True
except Exception as e:
    print(f"⚠️ LLM Director not available: {e}")
    HAS_LLM = False

app = FastAPI(title="NanoBanana Generator API")

# Allow CORS so you can call this from any frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def serve_pil_image(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

@app.get("/")
def read_root():
    return {"message": "NanoBanana Generator API is running. Go to /docs for more."}

@app.get("/models")
def get_models(
    api_key_header: str | None = Header(default=None, alias="X-API-Key"),
    base_url_header: str | None = Header(default=None, alias="X-Base-Url"),
):
    """Fetches available models from the LLM provider (Requesty/OpenAI-compatible).
    Prefers API Key and Base URL from headers; falls back to .env. Defaults base to Requesty router.
    """
    api_key = api_key_header or os.environ.get("OPENAI_API_KEY")
    base_url = (base_url_header or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")).rstrip('/')

    if not api_key or "placeholder" in str(api_key):
        return {"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]}

    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{base_url}/models", headers=headers, timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching models: {e}")
        return {"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}, {"id": "error-fetching-models"}]}

@app.get("/generate/parchment")
def get_parchment():
    """Generates a new unique Void Parchment texture."""
    img = create_void_parchment(index=None)
    return serve_pil_image(img)

@app.get("/generate/enso")
def get_enso():
    """Generates a new unique Ink Enso circle."""
    img = create_ink_enso(index=None)
    return serve_pil_image(img)

@app.get("/generate/directed/enso")
def get_directed_enso(
    prompt: str = Query(..., description="Describe the vibe (e.g. 'Burning Rage')"),
    model: str = Query("gpt-4o", description="The LLM model to use"),
    api_key_header: str | None = Header(default=None, alias="X-API-Key"),
    base_url_header: str | None = Header(default=None, alias="X-Base-Url"),
):
    """
    Uses LLM (Requesty/OpenAI-compatible) to generate an Enso from a text prompt.
    Prefers API Key and Base URL from headers; falls back to .env. Defaults base to Requesty router.
    """
    if not HAS_LLM:
        raise HTTPException(status_code=503, detail="LLM Director not available.")

    api_key = api_key_header or os.environ.get("OPENAI_API_KEY")
    base_url = base_url_header or os.environ.get("LLM_BASE_URL", "https://router.requesty.ai/v1")

    if not api_key or "placeholder" in str(api_key):
        raise HTTPException(status_code=401, detail="No API Key provided. Pass X-API-Key header or configure .env")

    try:
        params = get_enso_params_from_prompt(prompt, api_key=api_key, model=model, base_url=base_url)
        print(f"🎨 Director ({model}) ordered: {params}")

        rgb_color = hex_to_rgb(params.color_hex)
        img = create_ink_enso(
            index=None,
            color=rgb_color,
            complexity=params.complexity,
            chaos=params.chaos,
        )

        return serve_pil_image(img)

    except Exception as e:
        print(f"❌ Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate/sigil")
def get_sigil():
    """Generates a new unique Arcane Sigil."""
    img = create_sigil(index=None)
    return serve_pil_image(img)

@app.get("/generate/giraffe")
def get_giraffe():
    """Generates a new unique Ink Giraffe entity."""
    img = create_giraffe(index=None)
    return serve_pil_image(img)

@app.get("/generate/kangaroo")
def get_kangaroo():
    """Generates a new unique Ink Kangaroo on a Pogo Stick."""
    img = create_kangaroo(index=None)
    return serve_pil_image(img)

if __name__ == "__main__":
    import uvicorn
    print("🍌 NanoBanana API starting up...")
    print(f"   - LLM_BASE_URL: {os.environ.get('LLM_BASE_URL', 'Not Set (will use default)')}")
    key = os.environ.get('OPENAI_API_KEY', '')
    masked_key = f"{key[:8]}...{key[-4:]}" if key else "Not Set"
    print(f"   - OPENAI_API_KEY: {masked_key}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
