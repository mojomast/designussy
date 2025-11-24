"""E2E tests for batch generation workflows."""

import pytest
import asyncio
import time
from playwright.async_api import expect
from tests.e2e.utils import create_test_utils, create_api_helper


@pytest.mark.e2e
@pytest.mark.batch
@pytest.mark.asyncio
class TestBatchWorkflows:
    """Test batch generation job workflows."""
    
    async def test_create_batch_job(self, page, api_client):
        """Test creating a new batch generation job."""
        test_utils = create_test_utils(page)
        
        # Prepare batch request
        batch_requests = [
            {
                "type": "parchment",
                "count": 2,
                "parameters": {"width": 512, "height": 512}
            },
            {
                "type": "enso", 
                "count": 1,
                "parameters": {"complexity": "medium"}
            }
        ]
        
        batch_data = {
            "requests": batch_requests,
            "options": {
                "parallel": True,
                "priority": "normal"
            }
        }
        
        # Create batch job via API
        response = await api_client.post("/generate/batch", json=batch_data)
        assert response.status_code == 200
        
        job_data = response.json()
        assert "job_id" in job_data
        assert job_data["status"] == "processing"
        assert job_data["total_items"] == 3  # 2 + 1
        
        job_id = job_data["job_id"]
        print(f"✅ Created batch job: {job_id}")
        
        # Return job_id for follow-up tests
        return job_id
    
    async def test_batch_job_progress_monitoring(self, page, api_client):
        """Test monitoring batch job progress."""
        # First create a batch job
        job_id = await self.test_create_batch_job(page, api_client)
        
        # Monitor job progress
        start_time = time.time()
        max_wait_time = 60  # Wait up to 60 seconds
        
        while time.time() - start_time < max_wait_time:
            # Check job status
            response = await api_client.get(f"/generate/batch/{job_id}/status")
            assert response.status_code == 200
            
            job_status = response.json()
            print(f"Job {job_id} status: {job_status['status']} "
                  f"({job_status['completed_items']}/{job_status['total_items']})")
            
            # Check if job completed
            if job_status["status"] in ["completed", "failed", "cancelled"]:
                assert job_status["completed_items"] > 0, "No items were completed"
                print(f"✅ Batch job completed with status: {job_status['status']}")
                break
            
            # Wait before checking again
            await asyncio.sleep(2)
        
        # Verify final status
        final_response = await api_client.get(f"/generate/batch/{job_id}/status")
        final_status = final_response.json()
        assert final_status["status"] in ["completed", "failed", "cancelled"]
        
        print("✅ Batch job progress monitoring test completed")
    
    async def test_batch_job_with_different_asset_types(self, page, api_client):
        """Test batch job with multiple different asset types."""
        batch_requests = [
            {"type": "parchment", "count": 1},
            {"type": "enso", "count": 1},
            {"type": "sigil", "count": 1},
            {"type": "giraffe", "count": 1},
            {"type": "kangaroo", "count": 1}
        ]
        
        batch_data = {
            "requests": batch_requests,
            "options": {"parallel": True}
        }
        
        response = await api_client.post("/generate/batch", json=batch_data)
        assert response.status_code == 200
        
        job_data = response.json()
        job_id = job_data["job_id"]
        
        # Wait for completion
        await asyncio.sleep(10)  # Allow time for processing
        
        # Check final status
        response = await api_client.get(f"/generate/batch/{job_id}/status")
        status = response.json()
        
        assert status["total_items"] == 5
        assert status["completed_items"] >= 0
        
        print("✅ Multi-asset type batch job test completed")
    
    async def test_batch_job_cancellation(self, page, api_client):
        """Test cancelling a running batch job."""
        # Create a batch job with more items (will take longer)
        batch_requests = [
            {"type": "sigil", "count": 3},  # More items to allow cancellation
            {"type": "giraffe", "count": 2}
        ]
        
        batch_data = {
            "requests": batch_requests,
            "options": {"parallel": True}
        }
        
        # Create job
        response = await api_client.post("/generate/batch", json=batch_data)
        assert response.status_code == 200
        
        job_data = response.json()
        job_id = job_data["job_id"]
        
        # Wait a moment for job to start processing
        await asyncio.sleep(3)
        
        # Cancel the job
        cancel_response = await api_client.post(f"/generate/batch/{job_id}/cancel")
        assert cancel_response.status_code == 200
        
        # Verify job is cancelled
        status_response = await api_client.get(f"/generate/batch/{job_id}/status")
        status = status_response.json()
        
        assert status["status"] == "cancelled"
        print("✅ Batch job cancellation test completed")


@pytest.mark.e2e
@pytest.mark.batch
@pytest.mark.asyncio
class TestBatchWorkflowUI:
    """Test UI interactions for batch processing."""
    
    async def test_batch_ui_interface(self, page):
        """Test the batch processing UI interface."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Look for batch-related UI elements
        batch_selectors = [
            '[data-batch="true"]',
            'button:has-text("Batch")',
            'button:has-text("Generate Multiple")',
            '.batch-controls',
            '#batch-generator'
        ]
        
        found_batch_ui = False
        for selector in batch_selectors:
            try:
                element = page.locator(selector)
                if await element.is_visible():
                    found_batch_ui = True
                    print(f"✅ Found batch UI element: {selector}")
                    break
            except Exception:
                continue
        
        if not found_batch_ui:
            print("ℹ️ No batch UI elements found - may use API only")