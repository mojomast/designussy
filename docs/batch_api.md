# NanoBanana Batch Generation API

## Overview

The Batch Generation API enables efficient bulk asset creation by processing multiple generation requests in a single API call. This system provides:

- **Asynchronous Processing**: Jobs run in the background without blocking the client
- **Progress Tracking**: Real-time status updates on job progress
- **Job Management**: Cancel running jobs and list all active jobs
- **Rate Limiting**: Protection against abuse with configurable limits
- **Caching Integration**: Leverages existing cache system for performance
- **Error Handling**: Graceful handling of partial failures

## Architecture

### Batch Processing Flow

```
Client Request → Create Job → Background Processing → Status Polling → Results
                      ↓
                 Return Job ID
                      ↓
              Process Assets Async
                      ↓
           Update Progress & Status
                      ↓
          Client Retrieves Results
```

### Job Lifecycle

```
PENDING → PROCESSING → [COMPLETED | FAILED | CANCELLED]
```

## API Endpoints

### 1. Create Batch Job

**Endpoint**: `POST /generate/batch`

**Rate Limit**: 10 requests/minute

**Request Body**:
```json
{
  "requests": [
    {
      "type": "parchment",
      "count": 5
    },
    {
      "type": "enso",
      "count": 3
    },
    {
      "type": "sigil",
      "count": 2,
      "parameters": {
        "complexity": 3,
        "glow_intensity": 0.8
      }
    }
  ],
  "options": {
    "parallel": true,
    "notify_progress": false,
    "max_workers": 4
  }
}
```

**Response** (201 Created):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "total_items": 10,
  "completed_items": 0,
  "created_at": "2025-11-24T20:00:00.000Z",
  "message": "Batch job created and processing started"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request format or parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error during job creation

### 2. Get Job Status

**Endpoint**: `GET /generate/batch/{job_id}/status`

**Rate Limit**: 60 requests/minute

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "total_items": 10,
  "completed_items": 5,
  "failed_items": 1,
  "assets": [
    {
      "request_index": 0,
      "asset_index": 0,
      "asset_type": "parchment",
      "success": true,
      "timestamp": "2025-11-24T20:00:01.000Z"
    },
    {
      "request_index": 0,
      "asset_index": 1,
      "asset_type": "parchment",
      "success": true,
      "timestamp": "2025-11-24T20:00:02.000Z"
    },
    {
      "request_index": 1,
      "asset_index": 0,
      "asset_type": "enso",
      "success": false,
      "error": "Generation failed: Out of memory",
      "timestamp": "2025-11-24T20:00:03.000Z"
    }
  ],
  "created_at": "2025-11-24T20:00:00.000Z",
  "started_at": "2025-11-24T20:00:00.500Z",
  "completed_at": null,
  "error": null
}
```

**Status Values**:
- `pending`: Job created but not yet started
- `processing`: Job is currently running
- `completed`: Job finished successfully (may have some failures)
- `failed`: Job failed completely
- `cancelled`: Job was cancelled by user

**Error Responses**:
- `404 Not Found`: Job ID not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### 3. Cancel Job

**Endpoint**: `POST /generate/batch/{job_id}/cancel`

**Rate Limit**: 30 requests/minute

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Job cancelled successfully",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-24T20:01:00.000Z"
}
```

**Error Responses**:
- `404 Not Found`: Job ID not found or already completed
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### 4. List All Jobs

**Endpoint**: `GET /jobs`

**Rate Limit**: 30 requests/minute

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "total_items": 10,
      "completed_items": 9,
      "failed_items": 1,
      "created_at": "2025-11-24T20:00:00.000Z",
      "started_at": "2025-11-24T20:00:00.500Z",
      "completed_at": "2025-11-24T20:00:15.000Z",
      "error": null
    },
    {
      "job_id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "processing",
      "total_items": 5,
      "completed_items": 2,
      "failed_items": 0,
      "created_at": "2025-11-24T20:01:00.000Z",
      "started_at": "2025-11-24T20:01:00.200Z",
      "completed_at": null,
      "error": null
    }
  ],
  "total_jobs": 2,
  "timestamp": "2025-11-24T20:02:00.000Z"
}
```

## Request Schema

### GenerationRequest

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `type` | string | Yes | Asset type to generate | Must be one of: `parchment`, `enso`, `sigil`, `giraffe`, `kangaroo` |
| `count` | integer | Yes | Number of assets to generate | 1-1000 |
| `parameters` | object | No | Generation parameters | Varies by asset type |

### BatchOptions

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `parallel` | boolean | No | true | Enable parallel processing |
| `notify_progress` | boolean | No | false | Enable progress notifications (future feature) |
| `max_workers` | integer | No | 4 | Maximum parallel workers (1-20) |

### BatchRequest

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `requests` | array | Yes | Array of generation requests | 1-100 requests |
| `options` | object | No | Batch processing options | - |

**Total Count Constraint**: Sum of all `count` values across requests cannot exceed 1000.

## Usage Examples

### Example 1: Simple Batch Request

Generate 5 parchment textures and 3 enso circles:

```bash
curl -X POST http://localhost:8001/generate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"type": "parchment", "count": 5},
      {"type": "enso", "count": 3}
    ]
  }'
```

### Example 2: Polling for Status

Poll job status until completion:

```bash
# Create job
JOB_ID=$(curl -s -X POST http://localhost:8001/generate/batch \
  -H "Content-Type: application/json" \
  -d '{"requests": [{"type": "sigil", "count": 10}]}' | jq -r .job_id)

# Poll status
while true; do
  STATUS=$(curl -s "http://localhost:8001/generate/batch/$JOB_ID/status" | jq -r .status)
  echo "Job status: $STATUS"
  
  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" || "$STATUS" == "cancelled" ]]; then
    break
  fi
  
  sleep 2
done

# Get final results
curl -s "http://localhost:8001/generate/batch/$JOB_ID/status" | jq .
```

### Example 3: Cancelling a Job

```bash
# Cancel a running job
curl -X POST http://localhost:8001/generate/batch/550e8400-e29b-41d4-a716-446655440000/cancel
```

### Example 4: JavaScript/TypeScript Client

```javascript
// Create batch job
async function createBatchJob(requests, options = {}) {
  const response = await fetch('http://localhost:8001/generate/batch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      requests,
      options
    })
  });
  
  if (!response.ok) {
    throw new Error(`Batch job creation failed: ${response.status}`);
  }
  
  return await response.json();
}

// Poll job status
async function pollJobStatus(jobId, interval = 2000) {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const response = await fetch(`http://localhost:8001/generate/batch/${jobId}/status`);
        
        if (!response.ok) {
          reject(new Error(`Status check failed: ${response.status}`));
          return;
        }
        
        const status = await response.json();
        
        if (['completed', 'failed', 'cancelled'].includes(status.status)) {
          resolve(status);
        } else {
          setTimeout(poll, interval);
        }
      } catch (error) {
        reject(error);
      }
    };
    
    poll();
  });
}

// Usage
const job = await createBatchJob([
  { type: 'parchment', count: 5 },
  { type: 'enso', count: 3 }
]);

console.log(`Job created: ${job.job_id}`);

const result = await pollJobStatus(job.job_id);
console.log(`Job completed: ${result.completed_items}/${result.total_items} items`);
```

### Example 5: Python Client

```python
import requests
import time

def create_batch_job(requests, options=None):
    """Create a batch generation job"""
    url = "http://localhost:8001/generate/batch"
    payload = {
        "requests": requests,
        "options": options or {}
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def poll_job_status(job_id, interval=2):
    """Poll job status until completion"""
    url = f"http://localhost:8001/generate/batch/{job_id}/status"
    
    while True:
        response = requests.get(url)
        response.raise_for_status()
        status = response.json()
        
        if status['status'] in ['completed', 'failed', 'cancelled']:
            return status
        
        time.sleep(interval)

# Usage
job = create_batch_job([
    {"type": "parchment", "count": 5},
    {"type": "enso", "count": 3}
])

print(f"Job created: {job['job_id']}")

result = poll_job_status(job['job_id'])
print(f"Job completed: {result['completed_items']}/{result['total_items']} items")
```

## Error Handling

### Partial Failures

Batch jobs handle partial failures gracefully. If some assets fail to generate:

1. Failed assets are recorded with error messages
2. Successful assets are still processed and cached
3. Job status becomes `completed` (not `failed`) if any assets succeeded
4. The `failed_items` count indicates number of failures

### Common Error Scenarios

| Scenario | Status | Action |
|----------|--------|--------|
| All assets succeed | `completed` | No action needed |
| Some assets fail | `completed` | Check `failed_items` and error messages |
| All assets fail | `failed` | Review error messages and retry |
| Job cancelled | `cancelled` | User-initiated cancellation |
| Server error | `failed` | Check server logs and retry |

### Error Response Format

```json
{
  "detail": "Failed to create batch job: Invalid asset type 'invalid_type'"
}
```

## Performance Considerations

### Batch Size Guidelines

| Batch Size | Expected Processing Time | Memory Usage | Recommendation |
|------------|-------------------------|--------------|----------------|
| 1-10 items | 5-15 seconds | Low | Good for testing |
| 10-50 items | 15-60 seconds | Medium | Good for production |
| 50-100 items | 1-3 minutes | High | Monitor resources |
| 100+ items | 3+ minutes | Very High | Split into smaller batches |

### Rate Limiting

Rate limits protect the server from abuse:

- **Batch Creation**: 10 requests/minute
- **Status Checks**: 60 requests/minute
- **Job Cancellation**: 30 requests/minute
- **Job Listing**: 30 requests/minute

If you hit rate limits:
1. Implement exponential backoff in your client
2. Reduce polling frequency for status checks
3. Consider increasing batch size instead of frequency

### Caching Benefits

The batch API leverages the existing cache system:
- Assets are checked against cache before generation
- Generated assets are stored in cache for future requests
- Cache hits significantly improve performance
- Repeated batch jobs with same parameters are fast

## Configuration

### Environment Variables

See [`.env.example`](../.env.example) for all configuration options:

```bash
# Maximum items per batch
BATCH_MAX_ITEMS=100

# Parallel processing workers
BATCH_PARALLEL_WORKERS=4

# Job data TTL
BATCH_JOB_TTL=3600

# Rate limits
BATCH_RATE_LIMIT=10
BATCH_STATUS_RATE_LIMIT=60
BATCH_CANCEL_RATE_LIMIT=30
```

### Tuning Recommendations

**For Development**:
```bash
BATCH_MAX_ITEMS=10
BATCH_PARALLEL_WORKERS=2
BATCH_RATE_LIMIT=30
```

**For Production**:
```bash
BATCH_MAX_ITEMS=100
BATCH_PARALLEL_WORKERS=4
BATCH_RATE_LIMIT=10
```

**For High-Volume**:
```bash
BATCH_MAX_ITEMS=100
BATCH_PARALLEL_WORKERS=8
BATCH_RATE_LIMIT=5
```

## Best Practices

### 1. Request Design

- **Group similar assets**: Batch multiple requests of the same type
- **Reasonable counts**: Start with 10-20 items per batch
- **Use parameters**: Customize generation when needed
- **Test first**: Validate with small batches before scaling

### 2. Client Implementation

- **Poll responsibly**: Use 2-5 second intervals for status checks
- **Handle errors**: Implement retry logic with exponential backoff
- **Cancel unused jobs**: Clean up abandoned jobs
- **Monitor progress**: Display progress to users for large batches

### 3. Resource Management

- **Monitor memory**: Watch server memory usage with large batches
- **Clean up old jobs**: Jobs are automatically cleaned up after 24 hours
- **Use caching**: Leverage cache for repeated requests
- **Scale appropriately**: Adjust workers based on server capacity

### 4. Error Recovery

- **Check job status**: Always verify job completion
- **Handle partial failures**: Check `failed_items` count
- **Retry failed items**: Create new batch for failed assets
- **Log errors**: Save error messages for debugging

## Monitoring

### Key Metrics

Monitor these metrics for batch operations:

1. **Job Success Rate**: Percentage of jobs completing successfully
2. **Average Processing Time**: Time per job/item
3. **Cache Hit Rate**: Percentage of assets served from cache
4. **Failure Rate**: Percentage of individual asset failures
5. **Rate Limit Hits**: Frequency of rate limit violations

### Log Entries

Batch operations are logged with emojis:

```
📥 Request: {"method": "POST", "url": "http://localhost:8001/generate/batch", ...}
✅ Generated parchment #1/5 for job 550e8400...
❌ Failed to generate enso #2: Out of memory
🎉 Batch job 550e8400 completed: 9 successful, 1 failed
```

## Troubleshooting

### Job Stuck in "pending" Status

**Cause**: Server busy or background task queue full

**Solution**: Wait a few seconds and check status again

### High Failure Rate

**Cause**: Server resource exhaustion or invalid parameters

**Solution**: 
1. Check server logs for error messages
2. Reduce batch size
3. Verify asset parameters
4. Check available memory

### Rate Limit Errors

**Cause**: Too many requests in short time

**Solution**:
1. Implement exponential backoff
2. Reduce request frequency
3. Increase batch size (fewer requests)

### Jobs Not Completing

**Cause**: Server restart or crash during processing

**Solution**:
1. Check if job was cancelled
2. Verify server is running
3. Create new job if needed

## Future Enhancements

### Planned Features

1. **WebSocket Notifications**: Real-time progress updates
2. **Job Prioritization**: Priority queue for urgent jobs
3. **Bulk Download**: Zip file generation for completed batches
4. **Job Scheduling**: Scheduled batch generation
5. **Advanced Filtering**: Filter jobs by status, date, type
6. **Job Templates**: Save and reuse batch configurations
7. **Progress Callbacks**: HTTP callbacks for status updates
8. **Job Dependencies**: Chain multiple batch jobs

## References

- [Asset Structure](asset_structure.md): Details on generated assets
- [Caching System](caching.md): Cache architecture and configuration
- [API Overview](../README.md): General API documentation
- [`.env.example`](../.env.example): Configuration options
- [`utils/batch_job.py`](../utils/batch_job.py): Batch job implementation
- [`backend.py`](../backend.py): API endpoint implementation