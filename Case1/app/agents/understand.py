"""Content Understanding Agent - Analyzes video, images, and text content."""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

logger = logging.getLogger(__name__)


class ContentUnderstandingAgent:
    """Agent for understanding multimedia content."""
    
    def __init__(self):
        """Initialize the content understanding agent."""
        self.blip_processor = None
        self.blip_model = None
        self._init_models()
    
    def _init_models(self):
        """Initialize BLIP model for image captioning."""
        try:
            # Use small BLIP model for CPU efficiency
            model_name = "Salesforce/blip-image-captioning-base"
            self.blip_processor = BlipProcessor.from_pretrained(model_name)
            self.blip_model = BlipForConditionalGeneration.from_pretrained(model_name)
            
            # Move to CPU and set to eval mode
            self.blip_model.eval()
            if torch.cuda.is_available():
                self.blip_model = self.blip_model.cuda()
            
            logger.info("BLIP model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BLIP model: {e}")
            self.blip_processor = None
            self.blip_model = None
    
    def caption_image(self, image_path: str) -> str:
        """
        Generate caption for an image using BLIP.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Generated caption text
        """
        try:
            if not self.blip_model or not self.blip_processor:
                return "Image captioning unavailable"
            
            # Load and process image
            image = Image.open(image_path).convert('RGB')
            
            # Generate caption
            inputs = self.blip_processor(image, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                out = self.blip_model.generate(**inputs, max_length=50)
            
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            return caption
            
        except Exception as e:
            logger.error(f"Error captioning image {image_path}: {e}")
            return f"Failed to caption image"
    
    def analyze_screenshots(self, screenshot_dir: str, max_images: int = 20) -> List[Dict]:
        """
        Analyze screenshot images and generate captions.
        
        Args:
            screenshot_dir: Directory containing screenshots
            max_images: Maximum number of images to process
            
        Returns:
            List of image analysis results
        """
        results = []
        
        try:
            # Get image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
            image_files = []
            
            if os.path.exists(screenshot_dir):
                for file in os.listdir(screenshot_dir):
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        image_files.append(os.path.join(screenshot_dir, file))
            
            # Process images
            for image_path in image_files[:max_images]:
                caption = self.caption_image(image_path)
                results.append({
                    'file': os.path.basename(image_path),
                    'caption': caption,
                    'path': image_path
                })
                logger.info(f"Captioned {os.path.basename(image_path)}: {caption[:50]}...")
            
            if not results:
                # Add placeholder if no images found
                results.append({
                    'file': 'no_images_found',
                    'caption': 'No screenshot images available for analysis',
                    'path': None
                })
            
        except Exception as e:
            logger.error(f"Error analyzing screenshots: {e}")
            results.append({
                'file': 'error',
                'caption': f'Screenshot analysis failed: {str(e)}',
                'path': None
            })
        
        return results
    
    def analyze_video(self, gameplay_dir: str, utils_media) -> Dict:
        """
        Analyze video content including frames and audio transcript.
        
        Args:
            gameplay_dir: Directory containing gameplay videos
            utils_media: Media utilities module for video processing
            
        Returns:
            Video analysis results
        """
        result = {
            'video_file': None,
            'transcript': '',
            'frame_captions': [],
            'duration': 0
        }
        
        try:
            # Find first video file
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
            video_file = None
            
            if os.path.exists(gameplay_dir):
                for file in os.listdir(gameplay_dir):
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        video_file = os.path.join(gameplay_dir, file)
                        break
            
            if not video_file:
                logger.warning("No video file found in gameplay directory")
                result['transcript'] = "No video available for analysis"
                return result
            
            result['video_file'] = os.path.basename(video_file)
            
            # Get video info
            video_info = utils_media.get_video_info(video_file)
            result['duration'] = video_info.get('duration', 0)
            
            # Extract transcript
            logger.info(f"Extracting transcript from {video_file}")
            transcript = utils_media.extract_audio_transcript(video_file)
            result['transcript'] = transcript[:4000] if transcript else "No audio transcript available"
            
            # Extract and caption frames
            logger.info(f"Extracting frames from {video_file}")
            temp_frames_dir = os.path.join('./temp', 'frames')
            frame_paths = utils_media.extract_frames_from_video(
                video_file, 
                temp_frames_dir,
                interval_seconds=2.0,
                max_frames=20
            )
            
            # Caption extracted frames
            for frame_path in frame_paths[:20]:
                caption = self.caption_image(frame_path)
                result['frame_captions'].append({
                    'frame': os.path.basename(frame_path),
                    'caption': caption
                })
            
            # Clean up temp frames
            try:
                import shutil
                if os.path.exists(temp_frames_dir):
                    shutil.rmtree(temp_frames_dir)
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            result['transcript'] = f"Video analysis failed: {str(e)}"
        
        return result
    
    def analyze_text(self, game_file: str) -> Dict:
        """
        Analyze game description text file.
        
        Args:
            game_file: Path to game description file
            
        Returns:
            Text analysis results
        """
        result = {
            'content': '',
            'summary': '',
            'word_count': 0
        }
        
        try:
            if os.path.exists(game_file):
                with open(game_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Store content (limited to 4000 chars)
                result['content'] = content[:4000]
                result['word_count'] = len(content.split())
                
                # Create simple summary (first 500 chars)
                result['summary'] = content[:500] + ('...' if len(content) > 500 else '')
                
                logger.info(f"Analyzed text file: {result['word_count']} words")
            else:
                result['content'] = 'Game description file not found'
                result['summary'] = 'No game description available'
                
        except Exception as e:
            logger.error(f"Error analyzing text file: {e}")
            result['content'] = f'Text analysis failed: {str(e)}'
            result['summary'] = 'Error reading game description'
        
        return result
    
    def analyze(self, inputs: Dict, utils_media) -> Dict:
        """
        Main analysis method for all content types.
        
        Args:
            inputs: Dictionary with paths to content directories/files
            utils_media: Media utilities module
            
        Returns:
            Complete content analysis results
        """
        try:
            logger.info("Starting content understanding analysis")
            
            # Analyze screenshots
            logger.info(f"Analyzing screenshots from {inputs.get('screenshot_dir')}")
            screenshot_analysis = self.analyze_screenshots(
                inputs.get('screenshot_dir', './screenshot')
            )
            
            # Analyze video
            logger.info(f"Analyzing video from {inputs.get('gameplay_dir')}")
            video_analysis = self.analyze_video(
                inputs.get('gameplay_dir', './Gameplay'),
                utils_media
            )
            
            # Analyze text
            logger.info(f"Analyzing text from {inputs.get('game_file')}")
            text_analysis = self.analyze_text(
                inputs.get('game_file', './game.txt')
            )
            
            # Compile results
            results = {
                'status': 'success',
                'screenshots': {
                    'count': len(screenshot_analysis),
                    'captions': screenshot_analysis[:5]  # First 5 for summary
                },
                'video': {
                    'file': video_analysis['video_file'],
                    'duration': video_analysis['duration'],
                    'transcript': video_analysis['transcript'][:1000],  # Truncate for summary
                    'frame_captions': video_analysis['frame_captions'][:5]  # First 5 frames
                },
                'text': {
                    'summary': text_analysis['summary'],
                    'word_count': text_analysis['word_count']
                },
                'full_data': {
                    'all_screenshot_captions': screenshot_analysis,
                    'full_transcript': video_analysis['transcript'],
                    'all_frame_captions': video_analysis['frame_captions'],
                    'full_text': text_analysis['content']
                }
            }
            
            logger.info("Content understanding analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Content understanding failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'screenshots': {'count': 0, 'captions': []},
                'video': {'file': None, 'duration': 0, 'transcript': '', 'frame_captions': []},
                'text': {'summary': '', 'word_count': 0},
                'full_data': {}
            }