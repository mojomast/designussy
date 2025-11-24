"""
Integration tests for API endpoints.

Tests all FastAPI endpoints for generator functionality, caching,
batch processing, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
import json


class TestBasicEndpoints:
    """Test basic API endpoints."""
    
    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "NanoBanana Generator API is running" in data["message"]
    
    def test_generators_list(self, test_client):
        """Test generators list endpoint."""
        response = test_client.get("/generators")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "generators" in data
        assert "total_generators" in data


class TestGeneratorEndpoints:
    """Test individual generator endpoints."""
    
    def test_generate_sigil(self, test_client):
        """Test sigil generation endpoint."""
        response = test_client.get("/generate/sigil")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
    
    def test_generate_enso(self, test_client):
        """Test enso generation endpoint."""
        response = test_client.get("/generate/enso")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
    
    def test_generate_parchment(self, test_client):
        """Test parchment generation endpoint."""
        response = test_client.get("/generate/parchment")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
    
    def test_generate_giraffe(self, test_client):
        """Test giraffe generation endpoint."""
        response = test_client.get("/generate/giraffe")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
    
    def test_generate_kangaroo(self, test_client):
        """Test kangaroo generation endpoint."""
        response = test_client.get("/generate/kangaroo")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")


class TestModularEndpoints:
    """Test modular generator endpoints."""
    
    def test_modular_sigil(self, test_client):
        """Test modular sigil generation."""
        response = test_client.get("/generate/modular/sigil?width=256&height=256")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
    
    def test_modular_enso(self, test_client):
        """Test modular enso generation."""
        response = test_client.get("/generate/modular/enso?width=512&height=512")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
    
    def test_modular_invalid_generator(self, test_client):
        """Test modular generation with invalid generator type."""
        response = test_client.get("/generate/modular/invalid_type")
        assert response.status_code == 400


class TestCacheEndpoints:
    """Test cache-related endpoints."""
    
    def test_cache_stats(self, test_client):
        """Test cache statistics endpoint."""
        response = test_client.get("/cache/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "cache_stats" in data
    
    def test_cache_clear(self, test_client):
        """Test cache clear endpoint."""
        response = test_client.get("/cache/clear")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "Cache cleared" in data["message"]


class TestBatchEndpoints:
    """Test batch processing endpoints."""
    
    def test_create_batch_job(self, test_client):
        """Test creating a batch job."""
        batch_data = {
            "requests": [
                {"type": "sigil", "count": 2, "parameters": {}},
                {"type": "enso", "count": 1, "parameters": {}}
            ]
        }
        
        response = test_client.post("/generate/batch", json=batch_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "processing"
    
    def test_batch_status(self, test_client):
        """Test getting batch job status."""
        # First create a job
        batch_data = {
            "requests": [
                {"type": "sigil", "count": 1, "parameters": {}}
            ]
        }
        
        response = test_client.post("/generate/batch", json=batch_data)
        job_id = response.json()["job_id"]
        
        # Then check status
        response = test_client.get(f"/generate/batch/{job_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
    
    def test_list_jobs(self, test_client):
        """Test listing all jobs."""
        response = test_client.get("/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert "jobs" in data
        assert "total_jobs" in data


class TestErrorHandling:
    """Test API error handling."""
    
    def test_invalid_endpoint(self, test_client):
        """Test accessing invalid endpoint."""
        response = test_client.get("/invalid/endpoint")
        assert response.status_code == 404
    
    def test_invalid_batch_request(self, test_client):
        """Test invalid batch request."""
        invalid_data = {"invalid": "data"}
        
        response = test_client.post("/generate/batch", json=invalid_data)
        assert response.status_code == 422  # Validation error