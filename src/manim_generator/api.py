"""FastAPI application for generating videos from Manim scripts."""

import os
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from rich.console import Console

from manim_generator.utils.config import DEFAULT_CONFIG
from manim_generator.utils.file import save_code_to_file
from manim_generator.utils.rendering import extract_scene_class_names
from manim_generator.utils.video import adjust_video_duration, render_and_concat
from manim_generator.workflow import ManimWorkflow

app = FastAPI(
    title="Manim Video Generator API",
    description="API for generating videos from Manim scripts or descriptions using LLM",
    version="0.1.0",
)


class VideoGenerateRequest(BaseModel):
    """Request model for video generation from description."""

    video_data: str
    output_dir: str | None = None
    min_duration: float | None = None  # Minimum duration in seconds (default: 60)
    max_duration: float | None = None  # Maximum duration in seconds (default: 180)
    manim_model: str | None = None
    review_model: str | None = None
    review_cycles: int | None = None
    temperature: float | None = None


class ScriptRequest(BaseModel):
    """Request model for video generation from script."""

    script: str
    output_dir: str | None = None
    min_duration: float | None = None  # Minimum duration in seconds (default: 60)
    max_duration: float | None = None  # Maximum duration in seconds (default: 180)


class VideoResponse(BaseModel):
    """Response model for video generation."""

    success: bool
    video_path: str | None = None
    video_url: str | None = None
    message: str
    error: str | None = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Manim Video Generator API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/generate", response_model=VideoResponse)
async def generate_video_from_description(request: VideoGenerateRequest) -> VideoResponse:
    """
    Generate a video from a description using LLM (like manim-generate command).

    This endpoint uses the full workflow: generates Manim code from description,
    reviews and iterates on it, then renders the final video.

    Args:
        request: VideoGenerateRequest containing the video description

    Returns:
        VideoResponse with the path to the generated video or error message
    """
    # Validate video_data is not empty
    if not request.video_data or not request.video_data.strip():
        raise HTTPException(status_code=400, detail="video_data cannot be empty")

    # Create output directory
    if request.output_dir:
        output_dir = request.output_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        output_dir = f"output/api_{timestamp}_{unique_id}"

    os.makedirs(output_dir, exist_ok=True)

    # Build config from request or use defaults
    config = {
        "manim_model": request.manim_model or DEFAULT_CONFIG["manim_model"],
        "review_model": request.review_model or DEFAULT_CONFIG["review_model"],
        "review_cycles": request.review_cycles or DEFAULT_CONFIG["review_cycles"],
        "output_dir": output_dir,
        "manim_logs": False,
        "streaming": False,
        "temperature": request.temperature or DEFAULT_CONFIG["temperature"],
        "no_temperature": False,
        "vision_enabled": False,  # Can be enhanced later
        "reasoning": None,
        "provider": None,
        "success_threshold": DEFAULT_CONFIG["success_threshold"],
        "frame_extraction_mode": DEFAULT_CONFIG["frame_extraction_mode"],
        "frame_count": DEFAULT_CONFIG["frame_count"],
        "headless": True,  # Always headless for API
        "scene_timeout": DEFAULT_CONFIG["scene_timeout"],
    }

    # Run the workflow
    try:
        console = Console()
        workflow = ManimWorkflow(config, console)

        # Generate initial code
        current_code, main_messages = workflow.generate_initial_code(request.video_data)
        
        # Execute initial code
        success, last_frames, combined_logs, successful_scenes = workflow.execute_code(
            current_code, "Initial"
        )
        workflow.initial_success = success
        working_code = current_code if success else None

        # Review and update code
        current_code, new_working_code, combined_logs = workflow.review_and_update_code(
            current_code, combined_logs, last_frames, request.video_data, successful_scenes
        )
        working_code = new_working_code if new_working_code else working_code

        # Finalize and render (force rendering in headless mode)
        if working_code:
            saved_file = save_code_to_file(
                working_code, filename=f"{output_dir}/video.py"
            )
            workflow.artifact_manager.save_step_artifacts("final", code=working_code)
            
            # Always render in API mode
            video_path = render_and_concat(saved_file, output_dir, "final_video.mp4")
        else:
            return VideoResponse(
                success=False,
                message="Failed to generate working code after review cycles",
                error="No working code was generated. Check logs for details.",
            )

        if video_path and os.path.exists(video_path):
            # Set default duration constraints (1-3 minutes)
            min_duration = request.min_duration if request.min_duration is not None else 60.0
            max_duration = request.max_duration if request.max_duration is not None else 180.0

            # Adjust video duration if needed
            adjusted_path = adjust_video_duration(video_path, min_duration, max_duration)
            if adjusted_path and os.path.exists(adjusted_path):
                if adjusted_path != video_path and os.path.exists(adjusted_path):
                    try:
                        if os.path.exists(video_path):
                            os.remove(video_path)
                    except Exception:
                        pass
                    video_path = adjusted_path

            # Calculate relative path from output base for URL
            abs_path = os.path.abspath(video_path)
            output_base = os.path.abspath("output")
            if abs_path.startswith(output_base):
                relative_path = os.path.relpath(abs_path, output_base)
                video_url = f"/video/{relative_path}"
            else:
                video_url = f"/video/{os.path.basename(video_path)}"

            return VideoResponse(
                success=True,
                video_path=abs_path,
                video_url=video_url,
                message=f"Video generated successfully (duration: {min_duration}-{max_duration}s)",
            )
        else:
            return VideoResponse(
                success=False,
                message="Video rendering failed",
                error="Rendering process completed but video file not found",
            )

    except Exception as e:
        return VideoResponse(
            success=False,
            message="Error during video generation",
            error=str(e),
        )


@app.post("/generate/script", response_model=VideoResponse)
async def generate_video_from_script(request: ScriptRequest) -> VideoResponse:
    """
    Generate a video from a Manim script.

    Args:
        request: ScriptRequest containing the Manim script code

    Returns:
        VideoResponse with the path to the generated video or error message
    """
    # Validate script is not empty
    if not request.script or not request.script.strip():
        raise HTTPException(status_code=400, detail="Script cannot be empty")

    # Create output directory
    if request.output_dir:
        output_dir = request.output_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        output_dir = f"output/api_{timestamp}_{unique_id}"

    os.makedirs(output_dir, exist_ok=True)

    # Save script to temporary file
    script_filename = os.path.join(output_dir, "video.py")
    saved_file = save_code_to_file(request.script, filename=script_filename)

    if not saved_file:
        return VideoResponse(
            success=False,
            message="Failed to save script to file",
            error="File save error",
        )

    # Validate script syntax by extracting scene names
    try:
        scene_names = extract_scene_class_names(request.script)
        if isinstance(scene_names, Exception):
            return VideoResponse(
                success=False,
                message="Script has syntax errors",
                error=str(scene_names),
            )
        if not scene_names:
            return VideoResponse(
                success=False,
                message="No scene classes found in script",
                error="Script must contain at least one Scene class",
            )
    except Exception as e:
        return VideoResponse(
            success=False,
            message="Failed to parse script",
            error=str(e),
        )

    # Render the video
    try:
        video_path = render_and_concat(saved_file, output_dir, "final_video.mp4")

        if video_path and os.path.exists(video_path):
            # Set default duration constraints (1-3 minutes)
            min_duration = request.min_duration if request.min_duration is not None else 60.0
            max_duration = request.max_duration if request.max_duration is not None else 180.0

            # Adjust video duration if needed
            adjusted_path = adjust_video_duration(video_path, min_duration, max_duration)
            if adjusted_path and os.path.exists(adjusted_path):
                # If a new file was created, use it; otherwise use original
                if adjusted_path != video_path and os.path.exists(adjusted_path):
                    # Remove original if different file was created
                    try:
                        if os.path.exists(video_path):
                            os.remove(video_path)
                    except Exception:
                        pass
                    video_path = adjusted_path

            # Calculate relative path from output base for URL
            abs_path = os.path.abspath(video_path)
            output_base = os.path.abspath("output")
            if abs_path.startswith(output_base):
                relative_path = os.path.relpath(abs_path, output_base)
                video_url = f"/video/{relative_path}"
            else:
                # Fallback: use filename only
                video_url = f"/video/{os.path.basename(video_path)}"

            return VideoResponse(
                success=True,
                video_path=abs_path,
                video_url=video_url,
                message=f"Video generated successfully (duration: {min_duration}-{max_duration}s)",
            )
        else:
            return VideoResponse(
                success=False,
                message="Video rendering failed",
                error="Rendering process completed but video file not found",
            )
    except Exception as e:
        return VideoResponse(
            success=False,
            message="Error during video generation",
            error=str(e),
        )


@app.get("/video/{video_path:path}")
async def get_video(video_path: str):
    """
    Retrieve a generated video file.

    Args:
        video_path: Path to the video file (relative to output directory)

    Returns:
        FileResponse with the video file
    """
    # Security: prevent directory traversal
    if ".." in video_path:
        raise HTTPException(status_code=400, detail="Invalid video path: directory traversal not allowed")

    # Normalize path separators
    normalized_path = video_path.replace("\\", "/")

    # Look for video in output directories
    output_base = "output"
    video_file_path = os.path.join(output_base, normalized_path)

    # Resolve to absolute path and ensure it's within output_base
    abs_output_base = os.path.abspath(output_base)
    abs_video_path = os.path.abspath(video_file_path)

    if not abs_video_path.startswith(abs_output_base):
        raise HTTPException(status_code=400, detail="Invalid video path: outside output directory")

    if not os.path.exists(abs_video_path):
        raise HTTPException(status_code=404, detail="Video not found")

    if not os.path.isfile(abs_video_path):
        raise HTTPException(status_code=400, detail="Path is not a file")

    return FileResponse(
        abs_video_path,
        media_type="video/mp4",
        filename=os.path.basename(abs_video_path),
    )


def create_app() -> FastAPI:
    """Create and return the FastAPI application instance."""
    return app

