# 🍌 THE VOIDUSSY PROTOCOL: AGENT HANDBOOK

> *To the Agents who follow: Welcome to the Void. Here we do not write code; we unwrite reality.*

## 🌑 The Aesthetic: "voidussy"

This project is built on a specific design language. Maintain this vibe at all costs.

-   **Keywords**: Eldritch, Ink-stained, Ouroboros, Parchment, Void, Decay, Ephemeral.
-   **Colors**:
    -   `Void Black`: #0a0a0a
    -   `Bone Parchment`: #d4c5b0
    -   `Deep Ink`: #000000
    -   `Ghost Grey`: #333333
-   **Typography**:
    -   *Headers*: `Cinzel` (Ancient, authoritative)
    -   *Body*: `Cormorant Garamond` (Elegant, literary)
    -   *Data/Code*: `Special Elite` (Gritty, typed)

---

## ⚙️ The Engine: voidussy Generator

The core of this project is a procedural generation engine powered by Python (`Pillow` + `Numpy`). It creates assets from pure code—no external image files required.

### 1. The Generator Script (`generate_assets.py`)
This is the alchemical circle. It defines functions to draw shapes, apply noise, and simulate ink bleed.

**Key Functions:**
-   `create_void_parchment()`: Generates heavy grain textures.
-   `create_ink_enso()`: Draws imperfect, chaotic brush circles.
-   `create_sigil()`: Generates random geometric runes with glow.
-   `create_giraffe()`: (Legacy) Draws eldritch ink-giraffes. **Use this as a template for new creatures.**

**To Extend:**
1.  Open `generate_assets.py`.
2.  Define a new function `create_thing(index)`.
3.  Use `ImageDraw` to sketch shapes.
4.  Apply `ImageFilter.GaussianBlur(1)` to "inkify" it.

### 2. The API Backend (`backend.py`)
We serve these assets hot via FastAPI.

**Run it:**
```bash
pip install fastapi uvicorn pillow numpy
python backend.py
```
*Runs on Port 8001 by default.*

**Endpoints:**
-   `GET /generate/parchment`
-   `GET /generate/enso`
-   `GET /generate/sigil`
-   `GET /generate/giraffe`
-   *Add your new creations here in `backend.py`.*

---

## 🖥️ Frontend Integration

See `unwritten_worlds_loading_examples.html` for reference.

**The "Live API" Pattern:**
```javascript
async function fetchAsset(type) {
    // 1. Call the API
    const response = await fetch(`http://localhost:8001/generate/${type}`);
    
    // 2. Convert to Blob -> ObjectURL
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    
    // 3. Display
    document.getElementById('my-img').src = url;
}
```

---

## 🔮 Directives for Future Agents

1.  **Do Not Clean Up**: The noise is the feature. If it looks dirty/grainy, it's perfect.
2.  **Procedural Over Static**: Never import a PNG if you can generate it with math.
3.  **Embrace the Glitch**: If the generation creates artifacts, call it "corruption" and ship it.
4.  **Make it Go Brrr**: Optimization is good, but style is paramount.

*End of Protocol.*
