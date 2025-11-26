/**
 * Unwritten Worlds - Asset Registry
 * Central registry of all available visual assets for the Voidussy design language.
 */

window.UnwrittenAssets = {
    // Base path for all assets
    basePath: 'assets/static/elements/',

    // Asset categories
    categories: {
        backgrounds: 'backgrounds/',
        glyphs: 'glyphs/',
        creatures: 'creatures/',
        ui: 'ui/'
    },

    // Complete asset catalog
    catalog: {
        // === BACKGROUNDS ===
        backgrounds: {
            void_parchment: { count: 20, type: 'texture', description: 'Dark ancient parchment with void stains' },
            floating_island: { count: 20, type: 'element', description: 'Levitating rock island with mist' },
            void_crystal: { count: 20, type: 'element', description: 'Crystalline formation with faint glow' },
            ink_nebula: { count: 20, type: 'effect', description: 'Swirling ink clouds nebula' },
            ethereal_mist: { count: 20, type: 'overlay', description: 'Soft mist with subtle gradients' }
        },

        // === GLYPHS ===
        glyphs: {
            ink_enso: { count: 20, type: 'symbol', description: 'Zen enso circle brush stroke' },
            sigil: { count: 20, type: 'symbol', description: 'Mystical geometric sigil' },
            mystic_eye: { count: 20, type: 'symbol', description: 'All-seeing mystic eye' },
            rune_stone: { count: 20, type: 'symbol', description: 'Ancient rune stone marker' },
            void_rune: { count: 20, type: 'symbol', description: 'Glowing void-energy sigil' },
            ink_spiral: { count: 20, type: 'symbol', description: 'Tight ink spiral with splatters' },
            ethereal_feather: { count: 20, type: 'symbol', description: 'Translucent feather of ink' },
            astral_eye: { count: 20, type: 'symbol', description: 'Mystic eye with nebula pupil' },
            void_circuit: { count: 20, type: 'symbol', description: 'Circuit pattern with purple glow' }
        },

        // === CREATURES ===
        creatures: {
            giraffe: { count: 20, type: 'creature', description: 'Void giraffe with ink spots' },
            kangaroo: { count: 20, type: 'creature', description: 'Kangaroo on pogo stick' },
            void_manta: { count: 20, type: 'creature', description: 'Manta ray with flowing ink fins' },
            ink_crab: { count: 20, type: 'creature', description: 'Crab with jagged ink claws' },
            void_serpent: { count: 1, type: 'creature', description: 'Mystical serpent of shadows (AI-generated)' },
            spectral_serpent: { count: 20, type: 'creature', description: 'Vapor-like serpentine form' },
            void_hopper: { count: 20, type: 'creature', description: 'Small hopper with glowing core' },
            abyssal_jelly: { count: 20, type: 'creature', description: 'Floating jellyfish with tentacles' }
        },

        // === UI ELEMENTS ===
        ui: {
            ink_divider: { count: 20, type: 'divider', description: 'Horizontal ink brush divider' },
            void_orb: { count: 20, type: 'icon', description: 'Glowing orb with void energy' },
            broken_chain: { count: 20, type: 'icon', description: 'Fractured chain with ink cracks' },
            ink_splatter: { count: 20, type: 'overlay', description: 'Random splatter pattern' },
            mystic_frame: { count: 20, type: 'border', description: 'Decorative frame with void borders' },
            ancient_key: { count: 20, type: 'icon', description: 'Rune-etched ancient key' }
        }
    },

    /**
     * Get the full path to an asset
     * @param {string} category - Asset category (backgrounds, glyphs, creatures, ui)
     * @param {string} name - Asset name (e.g., 'void_parchment')
     * @param {number} index - Asset index (1-20, or 1 for unique assets)
     * @returns {string} Full path to the asset
     */
    getPath(category, name, index = 1) {
        if (!this.categories[category]) {
            console.error(`Invalid category: ${category}`);
            return null;
        }

        const asset = this.catalog[category]?.[name];
        if (!asset) {
            console.error(`Asset not found: ${category}/${name}`);
            return null;
        }

        if (index < 1 || index > asset.count) {
            console.error(`Invalid index ${index} for ${name} (available: 1-${asset.count})`);
            return null;
        }

        return `${this.basePath}${this.categories[category]}${name}_${index}.png`;
    },

    /**
     * Get a random asset from a category
     * @param {string} category - Asset category
     * @param {string} name - Asset name
     * @returns {string} Full path to a random variant
     */
    getRandom(category, name) {
        const asset = this.catalog[category]?.[name];
        if (!asset) {
            console.error(`Asset not found: ${category}/${name}`);
            return null;
        }

        const randomIndex = Math.floor(Math.random() * asset.count) + 1;
        return this.getPath(category, name, randomIndex);
    },

    /**
     * Get all variants of an asset
     * @param {string} category - Asset category
     * @param {string} name - Asset name
     * @returns {string[]} Array of paths to all variants
     */
    getAllVariants(category, name) {
        const asset = this.catalog[category]?.[name];
        if (!asset) {
            console.error(`Asset not found: ${category}/${name}`);
            return [];
        }

        return Array.from({ length: asset.count }, (_, i) =>
            this.getPath(category, name, i + 1)
        );
    },

    /**
     * Get all assets in a category
     * @param {string} category - Asset category
     * @returns {Object} Object with asset names as keys
     */
    getCategory(category) {
        return this.catalog[category] || {};
    },

    /**
     * Search assets by type
     * @param {string} type - Asset type (texture, symbol, creature, etc.)
     * @returns {Object} Object with matching assets
     */
    searchByType(type) {
        const results = {};

        Object.entries(this.catalog).forEach(([category, assets]) => {
            Object.entries(assets).forEach(([name, asset]) => {
                if (asset.type === type) {
                    if (!results[category]) results[category] = {};
                    results[category][name] = asset;
                }
            });
        });

        return results;
    },

    /**
     * Preload an asset
     * @param {string} category - Asset category
     * @param {string} name - Asset name
     * @param {number} index - Asset index
     * @returns {Promise<HTMLImageElement>}
     */
    preload(category, name, index = 1) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            const path = this.getPath(category, name, index);

            if (!path) {
                reject(new Error('Invalid asset path'));
                return;
            }

            img.onload = () => resolve(img);
            img.onerror = () => reject(new Error(`Failed to load: ${path}`));
            img.src = path;
        });
    },

    /**
     * Preload all variants of an asset
     * @param {string} category - Asset category
     * @param {string} name - Asset name
     * @returns {Promise<HTMLImageElement[]>}
     */
    preloadAll(category, name) {
        const paths = this.getAllVariants(category, name);
        return Promise.all(
            paths.map(path => new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = () => reject(new Error(`Failed to load: ${path}`));
                img.src = path;
            }))
        );
    }
};

// Log initialization
console.log('Unwritten Worlds: Asset Registry Loaded');
console.log(`Total assets available: ${Object.values(UnwrittenAssets.catalog)
        .reduce((sum, category) =>
            sum + Object.values(category).reduce((s, a) => s + a.count, 0), 0)
    }`);
