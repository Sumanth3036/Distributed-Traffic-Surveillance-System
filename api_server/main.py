from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import redis
import aio_pika
import uuid
import logging
import json
import os
from datetime import datetime

# ---------------------------
# Configuration
# ---------------------------

API_KEYS = {"traffic123"}
REDIS_HOST = "redis"
REDIS_PORT = 6379
RABBITMQ_URL = "amqp://guest:guest@rabbitmq/"
QUEUE_NAME = "task_queue"
RATE_LIMIT = 10

# ---------------------------
# Initialization
# ---------------------------

app = FastAPI(title="🚦 Distributed Traffic Surveillance API")
app.mount("/static", StaticFiles(directory="/app/static"), name="static")  # ✅ Serve annotated files

api_key_header = APIKeyHeader(name="X-API-Key")
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Authentication
# ---------------------------

def authenticate(api_key: str = Depends(api_key_header)):
    if api_key not in API_KEYS:
        logger.warning(f"Invalid API key used: {api_key}")
        raise HTTPException(status_code=403, detail="Unauthorized")
    return api_key

# ---------------------------
# Rate Limiting
# ---------------------------

def rate_limit(api_key: str):
    key = f"ratelimit:{api_key}"
    current = r.incr(key)
    if current == 1:
        r.expire(key, 60)
    elif current > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

# ---------------------------
# Unified Upload Endpoint
# ---------------------------

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), api_key: str = Depends(authenticate)):
    rate_limit(api_key)

    ext = file.filename.lower().split(".")[-1]
    if ext not in {"mp4", "avi", "mov", "mkv", "jpg", "jpeg", "png", "bmp"}:
        raise HTTPException(status_code=400, detail="Only video or image files are accepted.")

    file_type = "image" if ext in {"jpg", "jpeg", "png", "bmp"} else "video"
    contents = await file.read()
    task_id = str(uuid.uuid4())

    task = {
        "id": task_id,
        "filename": file.filename,
        "timestamp": datetime.utcnow().isoformat(),
        "source": api_key,
        "type": file_type,
        "data": contents.hex()
    }

    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.declare_queue(QUEUE_NAME, durable=True)

        await channel.default_exchange.publish(
            aio_pika.Message(body=str(task).encode()),
            routing_key=QUEUE_NAME
        )
        await connection.close()

        r.set(f"task:{task_id}:status", "queued")
        logger.info(f"📤 {file_type.capitalize()} Task {task_id} queued by {api_key}")

        return {"message": f"{file_type.capitalize()} uploaded successfully!", "task_id": task_id}

    except Exception as e:
        logger.error(f"❌ Failed to queue {file_type} task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while queuing")

# ---------------------------
# Result Fetch Endpoint
# ---------------------------

@app.get("/result/{task_id}")
def get_result(task_id: str):
    result = r.get(f"task:{task_id}:result")
    if result:
        return {
            "status": "done",
            "task_id": task_id,
            "result": result
        }

    status = r.get(f"task:{task_id}:status")
    if status:
        return {
            "status": status,
            "task_id": task_id
        }

    return {"status": "not_found", "task_id": task_id}

# ---------------------------
# Progress Endpoint (Real-time)
# ---------------------------

@app.get("/progress/{task_id}")
def get_progress(task_id: str):
    """Get real-time processing progress for a task"""
    progress_data = r.get(f"task:{task_id}:progress")
    if progress_data:
        return json.loads(progress_data)
    return {"status": "no_progress", "task_id": task_id}

# ---------------------------
# Download Endpoint
# ---------------------------

@app.get("/download/{task_id}")
def download_result(task_id: str):
    """Download the processed video/image with annotations"""
    result = r.get(f"task:{task_id}:result")
    if not result:
        raise HTTPException(status_code=404, detail="Task not found or not completed")
    
    result_data = json.loads(result)
    annotated_url = result_data.get("annotated_url", "")
    
    # Extract filename from URL
    filename = annotated_url.split("/")[-1]
    file_path = f"/app/static/annotated/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Processed file not found")
    
    # Determine media type
    file_type = result_data.get("type", "video")
    media_type = "image/jpeg" if file_type == "image" else "video/mp4"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ---------------------------
# Health Check
# ---------------------------

@app.get("/")
def health_check():
    return {"message": "🚦 Traffic Surveillance API is running properly!"}
