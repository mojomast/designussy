#!/usr/bin/env python3
"""
Test script for NanoBanana Batch Generation API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_create_batch_job():
    """Test creating a batch job"""
    print("=" * 60)
    print("TEST 1: Create Batch Job")
    print("=" * 60)
    
    url = f"{BASE_URL}/generate/batch"
    payload = {
        "requests": [
            {
                "type": "parchment",
                "count": 2
            },
            {
                "type": "enso",
                "count": 2
            },
            {
                "type": "sigil",
                "count": 1
            }
        ],
        "options": {
            "parallel": True,
            "notify_progress": False
        }
    }
    
    print(f"Request: POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            return response.json().get('job_id')
        else:
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_job_status(job_id):
    """Test getting job status"""
    print("\n" + "=" * 60)
    print("TEST 2: Get Job Status")
    print("=" * 60)
    
    url = f"{BASE_URL}/generate/batch/{job_id}/status"
    print(f"Request: GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        return response.json()
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_poll_job_completion(job_id, max_attempts=30):
    """Poll job status until completion"""
    print("\n" + "=" * 60)
    print("TEST 3: Poll Job Until Completion")
    print("=" * 60)
    
    for i in range(max_attempts):
        status = test_get_job_status(job_id)
        
        if not status:
            print("Failed to get status")
            break
            
        job_status = status.get('status')
        
        if job_status in ['completed', 'failed', 'cancelled']:
            print(f"\n✅ Job {job_status} after {i+1} attempts")
            return status
        
        print(f"Attempt {i+1}/{max_attempts}: Status is '{job_status}', waiting...")
        time.sleep(2)
    
    print(f"\n❌ Job did not complete after {max_attempts} attempts")
    return None

def test_list_jobs():
    """Test listing all jobs"""
    print("\n" + "=" * 60)
    print("TEST 4: List All Jobs")
    print("=" * 60)
    
    url = f"{BASE_URL}/jobs"
    print(f"Request: GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")

def test_cancel_job(job_id):
    """Test cancelling a job"""
    print("\n" + "=" * 60)
    print("TEST 5: Cancel Job")
    print("=" * 60)
    
    url = f"{BASE_URL}/generate/batch/{job_id}/cancel"
    print(f"Request: POST {url}")
    
    try:
        response = requests.post(url, timeout=10)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")

def test_error_cases():
    """Test error cases"""
    print("\n" + "=" * 60)
    print("TEST 6: Error Cases")
    print("=" * 60)
    
    # Test 1: Invalid asset type
    print("\n--- Test 6.1: Invalid Asset Type ---")
    url = f"{BASE_URL}/generate/batch"
    payload = {
        "requests": [
            {
                "type": "invalid_type",
                "count": 1
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Too many items
    print("\n--- Test 6.2: Too Many Items ---")
    payload = {
        "requests": [
            {
                "type": "parchment",
                "count": 1001
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Non-existent job status
    print("\n--- Test 6.3: Non-existent Job ---")
    url = f"{BASE_URL}/generate/batch/non-existent-job/status"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("NanoBanana Batch API Test Suite")
    print("=" * 60)
    
    # Wait for server to be ready
    print("\n⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test 1: Create batch job
    job_id = test_create_batch_job()
    
    if not job_id:
        print("\n❌ Failed to create batch job. Stopping tests.")
        return
    
    # Test 2: Poll until completion
    final_status = test_poll_job_completion(job_id)
    
    # Test 3: List all jobs
    test_list_jobs()
    
    # Test 4: Error cases
    test_error_cases()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    
    if final_status:
        print(f"\n📊 Final Job Summary:")
        print(f"   Status: {final_status.get('status')}")
        print(f"   Total Items: {final_status.get('total_items')}")
        print(f"   Completed: {final_status.get('completed_items')}")
        print(f"   Failed: {final_status.get('failed_items')}")

if __name__ == "__main__":
    main()