from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
from generate_assets import create_void_parchment, create_ink_enso, create_sigil, create_giraffe

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

@app.get("/")
def read_root():
    return {"message": "NanoBanana Generator API is running. Go to /docs for more."}

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

if __name__ == "__main__":
    import uvicorn
    print("🍌 NanoBanana API starting up...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
