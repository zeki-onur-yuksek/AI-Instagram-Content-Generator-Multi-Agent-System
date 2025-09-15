"""Media processing utilities for video and image handling."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
import ffmpeg
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def extract_frames_from_video(
    video_path: str, 
    output_dir: str, 
    interval_seconds: float = 2.0,
    max_frames: int = 20
) -> List[str]:
    """
    Extract frames from video at specified intervals.
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save extracted frames
        interval_seconds: Interval between frame extractions
        max_frames: Maximum number of frames to extract
        
    Returns:
        List of paths to extracted frame images
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get video duration
        probe = ffmpeg.probe(video_path)
        duration = float(probe['streams'][0]['duration'])
        
        frame_paths = []
        frame_count = 0
        
        for timestamp in range(0, int(duration), int(interval_seconds)):
            if frame_count >= max_frames:
                break
                
            output_path = os.path.join(output_dir, f"frame_{frame_count:04d}.jpg")
            
            try:
                (
                    ffmpeg
                    .input(video_path, ss=timestamp)
                    .output(output_path, vframes=1, loglevel='error')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                frame_paths.append(output_path)
                frame_count += 1
            except ffmpeg.Error as e:
                logger.warning(f"Failed to extract frame at {timestamp}s: {e}")
                continue
                
        logger.info(f"Extracted {len(frame_paths)} frames from {video_path}")
        return frame_paths
        
    except Exception as e:
        logger.error(f"Error extracting frames from video: {e}")
        # Fallback: try simple ffmpeg command
        try:
            output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', f'fps=1/{interval_seconds}',
                '-vframes', str(max_frames),
                output_pattern,
                '-y'
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Collect generated frames
            frame_paths = sorted([
                os.path.join(output_dir, f) 
                for f in os.listdir(output_dir) 
                if f.startswith('frame_') and f.endswith('.jpg')
            ])[:max_frames]
            
            return frame_paths
        except Exception as fallback_error:
            logger.error(f"Fallback frame extraction also failed: {fallback_error}")
            return []


def extract_audio_transcript(video_path: str, language: str = "auto") -> str:
    """
    Extract audio transcript from video using faster-whisper.
    
    Args:
        video_path: Path to video file
        language: Language code or "auto" for auto-detection
        
    Returns:
        Extracted transcript text
    """
    try:
        from faster_whisper import WhisperModel
        
        # Use small model for efficiency
        model = WhisperModel("small", device="cpu", compute_type="int8")
        
        # Transcribe
        segments, info = model.transcribe(
            video_path,
            language=None if language == "auto" else language,
            beam_size=5
        )
        
        # Combine segments
        transcript = " ".join([segment.text.strip() for segment in segments])
        
        logger.info(f"Extracted transcript ({info.language}): {len(transcript)} chars")
        return transcript
        
    except Exception as e:
        logger.error(f"Error extracting transcript: {e}")
        # Fallback: return empty or placeholder
        return "Transcript extraction failed - audio processing unavailable"


def resize_image_to_instagram(
    image_path: str, 
    output_path: str,
    target_size: Tuple[int, int] = (1080, 1350)
) -> str:
    """
    Resize and pad image to Instagram story format (4:5 ratio).
    
    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        target_size: Target dimensions (width, height)
        
    Returns:
        Path to processed image
    """
    try:
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA' or img.mode == 'LA':
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        
        # Calculate aspect ratios
        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        
        if abs(img_ratio - target_ratio) < 0.01:
            # Already correct ratio, just resize
            img = img.resize(target_size, Image.Resampling.LANCZOS)
        else:
            # Need to pad
            if img_ratio > target_ratio:
                # Image is wider, fit to width
                new_width = target_size[0]
                new_height = int(new_width / img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Add padding top and bottom
                padding = (target_size[1] - new_height) // 2
                result = Image.new('RGB', target_size, (255, 255, 255))
                result.paste(img, (0, padding))
                img = result
            else:
                # Image is taller, fit to height
                new_height = target_size[1]
                new_width = int(new_height * img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Add padding left and right
                padding = (target_size[0] - new_width) // 2
                result = Image.new('RGB', target_size, (255, 255, 255))
                result.paste(img, (padding, 0))
                img = result
        
        # Save processed image
        Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        
        logger.info(f"Processed image saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        # If processing fails, try to at least copy the original
        try:
            from shutil import copy2
            Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)
            copy2(image_path, output_path)
            return output_path
        except:
            return image_path


def get_video_info(video_path: str) -> dict:
    """Get basic video information."""
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
            None
        )
        
        if video_stream:
            return {
                'duration': float(probe['format'].get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'codec': video_stream.get('codec_name', 'unknown')
            }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
    
    return {
        'duration': 0,
        'width': 0,
        'height': 0,
        'fps': 0,
        'codec': 'unknown'
    }