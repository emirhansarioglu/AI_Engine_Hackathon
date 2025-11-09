from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, FileResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import uuid
from datetime import datetime
from typing import Optional
import asyncio

from config import Config
from pipeline.video_pipeline import VideoPipeline
from pipeline.pipeline_state import PipelineState, PipelineStage
from utils.logger import PipelineLogger

# Initialize FastAPI app
app = FastAPI(
    title="Video Generation Pipeline",
    description="Generate videos from images using Runware and add voice with Mirelo AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize services
Config.validate()
pipeline = VideoPipeline()
state_manager = PipelineState(Config.STATE_FILE)
logger = PipelineLogger(Config.LOG_FILE, Config.LOG_LEVEL)


# ============================================
# Routes
# ============================================

@app.get("/")
async def home(request: Request):
    """Render main page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image file
    
    Returns job_id and file info
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join("static/uploads", unique_filename)
        
        # Save file
        os.makedirs("static/uploads", exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Image uploaded: {file_path}")
        
        return JSONResponse({
            "success": True,
            "filename": unique_filename,
            "file_path": file_path,
            "original_filename": file.filename,
            "size": len(content)
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_video(
    background_tasks: BackgroundTasks,
    filename: str = Form(...),
    prompt: Optional[str] = Form(None),
    duration: int = Form(5),
    ratio: str = Form("16:9"),
    voice_text: Optional[str] = Form(None),
    voice_type: Optional[str] = Form("female")
):
    """
    Start video generation pipeline
    
    Returns job_id for tracking
    """
    try:
        # Generate job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Get image path
        image_path = os.path.join("static/uploads", filename)
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Start pipeline in background
        background_tasks.add_task(
            run_pipeline,
            job_id,
            image_path,
            prompt,
            duration,
            ratio,
        )
        
        logger.info(f"Started job: {job_id}")
        
        return JSONResponse({
            "success": True,
            "job_id": job_id,
            "message": "Video generation started"
        })
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """
    Get job status and progress
    """
    try:
        job = state_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Calculate progress percentage
        stage_progress = {
            PipelineStage.INITIALIZED.value: 10,
            PipelineStage.IMAGE_UPLOADED.value: 25,
            PipelineStage.VIDEO_GENERATED.value: 50,
            PipelineStage.VIDEO_DOWNLOADED.value: 75,
            PipelineStage.COMPLETED.value: 100,
            PipelineStage.FAILED.value: 0
        }
        
        progress = stage_progress.get(job['stage'], 0)
        
        response = {
            "success": True,
            "job_id": job_id,
            "stage": job['stage'],
            "progress": progress,
            "created_at": job['created_at'],
            "updated_at": job['updated_at']
        }
        
        # Add video URL if available
        if job['stage'] == PipelineStage.COMPLETED.value:
            response['video_url'] = job.get('final_video_path')
            response['runware_data'] = job.get('runware_data', {})
        
        # Add errors if any
        if job.get('errors'):
            response['errors'] = job['errors']
        
        return JSONResponse(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
async def list_jobs():
    """
    List all jobs with their status
    """
    try:
        summary = state_manager.get_summary()
        all_jobs = []
        
        for job_id, job_data in state_manager.states.items():
            all_jobs.append({
                'job_id': job_id,
                'stage': job_data['stage'],
                'created_at': job_data['created_at'],
                'image_path': job_data.get('image_path', '')
            })
        
        # Sort by creation time (newest first)
        all_jobs.sort(key=lambda x: x['created_at'], reverse=True)
        
        return JSONResponse({
            "success": True,
            "summary": summary,
            "jobs": all_jobs[:20]  # Return last 20 jobs
        })
        
    except Exception as e:
        logger.error(f"List jobs error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{job_id}")
async def download_video(job_id: str):
    """
    Download the final video
    """
    try:
        job = state_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job['stage'] != PipelineStage.COMPLETED.value:
            raise HTTPException(status_code=400, detail="Video not ready yet")
        
        video_path = job.get('final_video_path')
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"{job_id}.mp4"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Background Task
# ============================================

async def run_pipeline(
    job_id: str,
    image_path: str,
    prompt: Optional[str],
    duration: int,
    ratio: str
):
    """
    Run the complete pipeline in background
    """
    try:
        result = await pipeline.process_image(
            image_path=image_path,
            prompt=prompt,
            duration=duration,
            ratio=ratio,
            job_id=job_id
        )
        
        if result['success']:
            logger.info(f"Pipeline completed: {job_id}")
        else:
            logger.error(f"Pipeline failed: {job_id} - {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Pipeline exception: {job_id} - {str(e)}")
        state_manager.add_error(job_id, str(e))


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Video Pipeline API...")
    Config.validate()
    logger.info("API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Video Pipeline API...")
    await pipeline.cleanup()
    logger.info("Shutdown complete")


# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )