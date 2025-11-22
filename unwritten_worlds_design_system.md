# 🌑 Unwritten Worlds: Design System & Orchestration Guide

> *A manual for weaving the void.*

This document details the atomic elements of the "Unwritten Worlds" aesthetic and provides a guide for orchestrating them into complex, cinematic sequences.

---

## 1. Atomic Elements (The Ink)

### Colors & Variables
Define these in your CSS root to maintain the vibe.
```css
:root {
    --bg-color: #0a0a0a;      /* Void Black */
    --text-color: #e0e0e0;    /* Ghost White */
    --accent-color: #d4c5b0;  /* Bone Parchment */
    --ink-color: #000000;     /* Deep Ink */
}
```

### Typography
- **Headers**: `Cinzel` (Capitalized, letter-spacing: 0.2em) - *The Voice of Gods*
- **Body**: `Cormorant Garamond` (Italic or Regular) - *The Historian's Note*
- **Code/Data**: `Special Elite` - *The Glitch in Reality*

### CSS Primitives
Use these classes to apply instant styling.

**1. The Texture Overlay**
Always place this fixed `div` at the top of your `body` to grain-ify the entire screen.
```html
<div class="texture-overlay"></div>
<style>
.texture-overlay {
    position: fixed; inset: 0; pointer-events: none; opacity: 0.08;
    background-image: url("data:image/svg+xml,..."); /* See source */
    z-index: 9999;
}
</style>
```

**2. The Breathing Rune**
A circle that expands and contracts.
```html
<div class="rune-circle"><div class="rune-inner"></div></div>
```

---

## 2. Animation Primitives (The Motion)

The framework includes several keyframes you can reuse.

| Animation | Description | Usage |
| :--- | :--- | :--- |
| `drawEnso` | Rotates and reveals a stroke path. | SVG Paths (Stroke-dasharray trick) |
| `pulseText` | Subtle scale/opacity loop. | "Loading..." text |
| `flicker` | Glitchy opacity and text-shadow. | Runes, Artifacts |
| `voidHop` | Parabolic jump arc. | Kangaroos, Projectiles |
| `ink-spread` | SVG Filter for turbulent distortion. | Apply via `filter: url(#ink-spread)` |

**Example: Applying Ink Bleed**
```css
.my-element {
    filter: url(#ink-spread); /* Requires the SVG filter definition in DOM */
}
```

---

## 3. Orchestration (The Spell)

To create a "cinematic" loading screen (e.g., "Enso draws -> Text appears -> Glitch out"), do not rely solely on CSS delays. Use **JavaScript Promises** to act as a "Director".

### The Director Pattern

Create a helper to wait for animations:
```javascript
const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
```

### Example Script: "The Summoning"

```javascript
async function playSummoningSequence() {
    const enso = document.getElementById('enso');
    const text = document.getElementById('text');
    
    // Phase 1: Draw the Circle
    enso.style.animation = "drawEnso 3s ease-out forwards";
    await wait(3000); // Wait for draw to finish
    
    // Phase 2: Reveal Text
    text.style.opacity = "1";
    text.classList.add('flicker-effect');
    await wait(2000);
    
    // Phase 3: The Unwriting (Dissolve)
    document.body.style.transition = "filter 1s";
    document.body.style.filter = "blur(10px) grayscale(100%)";
    await wait(1000);
    
    // Complete
    window.location.href = "/game";
}
```

---

## 4. Procedural Integration (The NanoBanana)

When using the Python Backend (`port 8001`), fetch assets dynamically to ensure no two loading screens are identical.

**Orchestration Tip:**
Preload the asset *before* starting the scene.

```javascript
async function initScene() {
    // 1. Fetch unique asset
    const res = await fetch('http://localhost:8001/generate/sigil');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    
    // 2. Inject into DOM (hidden)
    const img = document.createElement('img');
    img.src = url;
    img.style.opacity = '0';
    document.getElementById('stage').appendChild(img);
    
    // 3. Reveal with drama
    await wait(100);
    img.style.transition = "opacity 2s ease-in";
    img.style.opacity = "1";
}
```

---

## 5. Future Recipes

Combine these elements to build new scenes:

-   **"The Library"**: Fetch 5 *Parchments*. Stack them with random rotations. Fade them out one by one.
-   **"The Stampede"**: Fetch 10 *Kangaroos*. Animate them hopping across the screen at different speeds (`animation-duration`).
-   **"The Oracle"**: Fetch a *Sigil*. Use `flicker` animation. Overlay "Deciphering..." text in `Special Elite` font.

*Go forth and unwrite.*
