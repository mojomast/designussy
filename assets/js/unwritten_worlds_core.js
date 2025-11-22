/**
 * Unwritten Worlds - Core JS Library
 * Handles SVG filter injection and animation orchestration.
 */

(function () {
    // 1. Inject SVG Filters into the DOM
    const svgFilters = `
    <svg width="0" height="0" style="position: absolute; pointer-events: none;">
        <defs>
            <!-- Filter for rough, ink-like edges -->
            <filter id="brush-stroke" x="-20%" y="-20%" width="140%" height="140%">
                <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="4" result="noise" />
                <feDisplacementMap in="SourceGraphic" in2="noise" scale="8" />
                <feGaussianBlur stdDeviation="0.5" result="blurred" />
                <feComposite operator="in" in="SourceGraphic" in2="blurred" result="composite" />
            </filter>

            <!-- Filter for paper texture/grit on text -->
            <filter id="rough-paper">
                <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" result="noise" />
                <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" in="noise" result="coloredNoise" />
                <feComposite operator="in" in="SourceGraphic" in2="coloredNoise" result="composite" />
            </filter>
            
            <!-- Ink Spread / Bleed Effect -->
            <filter id="ink-spread">
                <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" result="noise" />
                <feDisplacementMap in="SourceGraphic" in2="noise" scale="4" />
            </filter>

            <!-- Rough Edge Filter -->
            <filter id="rough-edge">
                <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" result="noise" />
                <feDisplacementMap in="SourceGraphic" in2="noise" scale="4" />
            </filter>

            <!-- Ink Bleed Filter (Color Channel Shift) -->
            <filter id="ink-bleed">
                <feTurbulence type="turbulence" baseFrequency="0.05" numOctaves="2" result="turbulence"/>
                <feDisplacementMap in2="turbulence" in="SourceGraphic" scale="3" xChannelSelector="R" yChannelSelector="G"/>
                <feGaussianBlur stdDeviation="0.5" />
            </filter>

            <!-- Eroded/Decayed Filter -->
            <filter id="eroded">
                <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="1" result="noise" />
                <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 6 -3" in="noise" result="coloredNoise" />
                <feComposite operator="out" in="SourceGraphic" in2="coloredNoise" result="composite" />
            </filter>
        </defs>
    </svg>
    `;

    const div = document.createElement('div');
    div.innerHTML = svgFilters;
    document.body.insertBefore(div, document.body.firstChild);

    console.log("Unwritten Worlds: SVG Filters Injected.");

})();

// 2. Orchestration Helpers (Global)

window.Unwritten = {
    /**
     * Wait for a specified number of milliseconds.
     * @param {number} ms 
     * @returns {Promise}
     */
    wait: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

    /**
     * Randomly flickers an element.
     * @param {HTMLElement} element 
     */
    glitch: async (element) => {
        if (!element) return;
        const originalOpacity = element.style.opacity;

        for (let i = 0; i < 5; i++) {
            element.style.opacity = Math.random();
            await window.Unwritten.wait(50 + Math.random() * 100);
        }
        element.style.opacity = originalOpacity;
    }
};
