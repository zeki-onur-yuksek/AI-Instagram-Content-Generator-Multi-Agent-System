"""FastAPI application for content generation pipeline."""

import os
import logging
from typing import Optional
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

from app.controller import ContentPipelineController

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="JoyCase1 Content Pipeline",
    description="Automated content generation pipeline for social media",
    version="1.0.0"
)

# Initialize controller
controller = None


@app.on_event("startup")
async def startup_event():
    """Initialize the pipeline controller on startup."""
    global controller
    try:
        openai_key = os.getenv('OPENAI_API_KEY')
        controller = ContentPipelineController(openai_api_key=openai_key)
        logger.info("Content pipeline controller initialized")
    except Exception as e:
        logger.error(f"Failed to initialize controller: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"ok": True}


@app.post("/run")
async def run_pipeline(
    mode: str = Form(default="local"),
    gameplay_dir: Optional[str] = Form(default=None),
    screenshot_dir: Optional[str] = Form(default=None),
    aso_file: Optional[str] = Form(default=None),
    game_file: Optional[str] = Form(default=None),
    drive_creds_json: Optional[str] = Form(default=None),
    drive_folder_id: Optional[str] = Form(default=None)
):
    """
    Run the content generation pipeline.
    
    Args:
        mode: 'local' or 'drive' mode
        gameplay_dir: Path to gameplay videos directory (local mode)
        screenshot_dir: Path to screenshots directory (local mode)
        aso_file: Path to ASO keywords file (local mode)
        game_file: Path to game description file (local mode)
        drive_creds_json: Path to Google Drive credentials JSON (drive mode)
        drive_folder_id: Google Drive folder ID (drive mode)
    
    Returns:
        Pipeline execution results with output paths
    """
    try:
        if not controller:
            raise HTTPException(status_code=500, detail="Controller not initialized")
        
        logger.info(f"Starting pipeline run in {mode} mode")
        
        # Prepare kwargs based on mode
        kwargs = {}
        
        if mode == "drive":
            # Use provided credentials or fall back to environment
            kwargs['drive_creds_json'] = drive_creds_json or os.getenv('DRIVE_CREDS_JSON')
            kwargs['drive_folder_id'] = drive_folder_id or os.getenv('DRIVE_FOLDER_ID')
            
            if not kwargs['drive_creds_json'] or not kwargs['drive_folder_id']:
                raise HTTPException(
                    status_code=400,
                    detail="Drive credentials and folder ID required for drive mode"
                )
        else:
            # Local mode parameters
            kwargs['gameplay_dir'] = gameplay_dir
            kwargs['screenshot_dir'] = screenshot_dir
            kwargs['aso_file'] = aso_file
            kwargs['game_file'] = game_file
        
        # Run the pipeline
        results = controller.run_pipeline(mode=mode, **kwargs)
        
        # Check if pipeline completed successfully
        if results['status'] == 'completed':
            response = {
                'status': 'success',
                'final_post_json': results['final_outputs']['json_path'],
                'package_zip': results['final_outputs']['package_path'],
                'outputs_dir': results['final_outputs']['outputs_directory'],
                'summary': 'Pipeline completed successfully',
                'details': {
                    'stages_completed': len([s for s in results['stages'].values() if s.get('status') == 'success']),
                    'total_stages': len(results['stages']),
                    'timestamp': results['timestamp']
                }
            }
            
            # Log success
            logger.info(f"Pipeline completed: {response['outputs_dir']}")
            
            return JSONResponse(content=response)
        else:
            # Pipeline failed
            error_msg = results.get('error', 'Unknown error occurred')
            logger.error(f"Pipeline failed: {error_msg}")
            
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get pipeline status."""
    if not controller:
        return {"status": "not_initialized"}
    
    return controller.get_pipeline_status()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "JoyCase1 Content Pipeline API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health - Health check",
            "run": "/run - Run content pipeline (POST)",
            "status": "/status - Get pipeline status"
        },
        "documentation": "/docs"
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )