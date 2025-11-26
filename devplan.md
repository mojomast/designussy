
# Devplan – Refactored BananaJam Backend

## Objective
Rebuild the BananaJam backend into a clean, modular, maintainable FastAPI architecture. Replace the old 3600-line monolithic `backend.py` with a structured multi-file system that reduces file size, increases clarity, and supports future features (assets, diversity system, job system, cache system).

---

## High-Level Goals
- Decompose all logic into **small files** grouped by concern.
- Fully support the **Upgraded Asset System** (`upgraded_asset_system/`).
- Preserve or intentionally redesign the **API surface** expected by the frontend.
- Use a **service layer** to isolate logic from HTTP routing.
- Use `models/` for schemas and domain objects.
- Prepare for job runners, background workers, or caches without bloating route files.
- Keep all modules <300 lines whenever possible.

---

## Directory Structure (Final Target)

```
bananajam_backend/
    main.py
    config.py

    api/
        routes/
            health.py
            assets.py
            generators.py
            diversity.py
            jobs.py
            cache.py

    models/
        requests.py
        responses.py
        domain.py

    services/
        asset_service.py
        diversity_service.py
        job_service.py
        cache_service.py

    upgraded_integration/
        registry.py

    infrastructure/
        logging.py
        storage.py
        scheduler.py (optional)
```

---

## Phase 0 – Backup & Initialization
- [ ] Move the old `backend.py` → `backend_legacy.py`
- [ ] Initialize new folder structure
- [ ] Commit baseline to git

---

## Phase 1 – Extract API Surface
List endpoints supported today or desired:

### Health
- `GET /health`

### Asset Listing
- `GET /assets`
- `GET /generators` (legacy compatibility)

### Generation
- `POST /generate`
- `POST /generate/batch`
- Future: `/generate/<special-endpoint>`

### Diversity System
- `GET /diversity/status`
- `POST /diversity/optimize/{type_id}`
- `POST /diversity/generate-diverse-batch`

### Batch Job System
- `GET /generate/batch/jobs`
- `GET /generate/batch/status/{job_id}`

### Cache Maintenance
- `GET /cache/status`
- `POST /cache/clear`

Document these in `API_SURFACE.md`.

---

## Phase 2 – Create `main.py` and Application Core
- Build minimal FastAPI app with:
  - CORS
  - Router includes
  - Startup log
- No business logic should live here.

---

## Phase 3 – Implement Modular Routers

### 3.1 Health Router (`health.py`)
Contains:
- `/health`
- Optional system metrics
- Calls services for status

### 3.2 Asset / Generator Router (`assets.py`, `generators.py`)
Contains:
- `/generators`
- `/assets`
- `/generate`
- `/generate/batch`
Delegates all logic to `asset_service`.

### 3.3 Diversity Router (`diversity.py`)
Contains:
- Diversity model stats
- Optimization endpoints
- Batch diversity generation

Routes call `diversity_service`.

### 3.4 Job Router (`jobs.py`)
Contains:
- `/generate/batch/jobs`
- `/generate/batch/status/{job_id}`
Logic delegated to `job_service`.

### 3.5 Cache Router (`cache.py`)
Contains endpoints for cache operations.

---

## Phase 4 – Build the Service Layer

### 4.1 Asset Service (`asset_service.py`)
Responsibilities:
- Interaction with Upgraded Asset System  
- Calling asset generators  
- Handling unknown asset names  
- Central logging  
- Normalized error responses  

### 4.2 Diversity Service (`diversity_service.py`)
Responsibilities:
- Diversity model configuration
- Running diversity optimizations
- Generating diverse batches
- Validation of types and constraints

### 4.3 Job Service (`job_service.py`)
Responsibilities:
- Job creation
- Job state storage (memory or disk)
- Job retrieval
- Job completion/error handling

### 4.4 Cache Service (`cache_service.py`)
Responsibilities:
- Cache directory listings
- Cache invalidation
- Integration with future asset caching backends

---

## Phase 5 – Domain Models

### `models/requests.py`
- `GenerateRequest`
- `BatchItem`
- `BatchGenerateRequest`
- Diversity request models

### `models/domain.py`
- `Job`
- `JobStatus`
- `DiversityStats`
- Asset metadata types

### `models/responses.py`
Optional but recommended for strong typing and frontend contracts.

---

## Phase 6 – Integration Layer (`upgraded_integration/registry.py`)
- Load `ASSET_REGISTRY` safely.
- Fallback if unavailable.
- Provide helpers like `call_asset(name, index, theme)`.

Keep the Upgraded Asset System isolated here so replacing it later requires minimal code changes.

---

## Phase 7 – Infrastructure Layer

### logging.py
- Central logger factory
- Replace ad-hoc `print()` calls gradually

### storage.py
- Paths for cache
- File I/O helpers
- Layout rules

### scheduler.py
Optional for background workers.

---

## Phase 8 – Migration Path

### Strategy:
1. Start with MVP routes (health, assets, generate).
2. Add diversity routes.
3. Add job routes.
4. Add cache and others only when the structure is stable.

Avoid copying old code blindly—rewrite cleanly, migrating logic in small chunks.

---

## Phase 9 – Testing & Verification

Use:
```bash
pytest
httpx
fastapi.testclient
```

Test areas:
- Asset listing
- Single generation
- Batch generation
- Diversity optimization
- Job tracking
- Cache clearing

---

## Phase 10 – Deployment Readiness
- Prepare Dockerfile
- Use gunicorn/uvicorn workers for production
- Ensure environment variables handled in config.py

---

## Final Notes
This devplan ensures the backend becomes easy to extend, maintain, and debug.  
No more >3000-line files.  
Modular, service-oriented, clean.  
Perfect for BananaJam’s long-term growth.
