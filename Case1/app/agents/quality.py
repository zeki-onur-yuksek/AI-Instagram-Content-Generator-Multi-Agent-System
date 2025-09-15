"""Quality Control Agent - Validates and improves content quality."""

import os
import re
import logging
from typing import Dict, List, Tuple
from pathlib import Path
from PIL import Image
import shutil

logger = logging.getLogger(__name__)


class QualityControlAgent:
    """Agent for quality control and content validation."""
    
    def __init__(self):
        """Initialize the quality control agent."""
        self.instagram_specs = {
            'story': {
                'width': 1080,
                'height': 1350,
                'aspect_ratio': 4/5
            },
            'post': {
                'width': 1080,
                'height': 1080,
                'aspect_ratio': 1.0
            }
        }
        
        self.text_limits = {
            'title_max': 60,
            'caption_max': 2200,
            'hashtag_max': 12,
            'hashtag_min': 5
        }
    
    def validate_image(self, image_path: str) -> Dict:
        """
        Validate image specifications.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Validation results
        """
        try:
            img = Image.open(image_path)
            width, height = img.size
            aspect_ratio = width / height
            
            # Check minimum resolution
            min_width = 1080
            min_height = 1350
            
            is_valid = width >= min_width and height >= min_height
            needs_resize = not (width == min_width and height == min_height)
            
            # Check aspect ratio (allow some tolerance)
            target_ratio = self.instagram_specs['story']['aspect_ratio']
            ratio_diff = abs(aspect_ratio - target_ratio)
            needs_padding = ratio_diff > 0.05
            
            return {
                'path': image_path,
                'current_size': (width, height),
                'current_ratio': aspect_ratio,
                'is_valid': is_valid,
                'needs_resize': needs_resize,
                'needs_padding': needs_padding,
                'issues': []
            }
            
        except Exception as e:
            logger.error(f"Error validating image {image_path}: {e}")
            return {
                'path': image_path,
                'error': str(e),
                'is_valid': False,
                'needs_resize': True,
                'needs_padding': True,
                'issues': [f'Failed to validate: {e}']
            }
    
    def process_images(self, image_paths: List[str], output_dir: str, utils_media) -> List[str]:
        """
        Process and validate all images.
        
        Args:
            image_paths: List of image paths to process
            output_dir: Directory to save processed images
            utils_media: Media utilities module
            
        Returns:
            List of processed image paths
        """
        processed = []
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for image_path in image_paths:
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}")
                continue
            
            validation = self.validate_image(image_path)
            
            output_path = os.path.join(
                output_dir, 
                f"processed_{os.path.basename(image_path)}"
            )
            
            if validation['needs_resize'] or validation['needs_padding']:
                # Process image to Instagram story format
                logger.info(f"Processing image: {image_path}")
                try:
                    processed_path = utils_media.resize_image_to_instagram(
                        image_path,
                        output_path,
                        target_size=(1080, 1350)
                    )
                    processed.append(processed_path)
                except Exception as e:
                    logger.error(f"Failed to process image: {e}")
                    # Copy original as fallback
                    shutil.copy2(image_path, output_path)
                    processed.append(output_path)
            else:
                # Image is already valid, just copy
                shutil.copy2(image_path, output_path)
                processed.append(output_path)
        
        logger.info(f"Processed {len(processed)} images")
        return processed
    
    def validate_text(self, title: str, caption: str, hashtags: List[str]) -> Dict:
        """
        Validate text content against limits and rules.
        
        Args:
            title: Post title
            caption: Post caption
            hashtags: List of hashtags
            
        Returns:
            Validation results with cleaned content
        """
        issues = []
        
        # Clean and validate title
        clean_title = title.strip()
        if len(clean_title) > self.text_limits['title_max']:
            clean_title = clean_title[:self.text_limits['title_max']]
            issues.append(f"Title truncated to {self.text_limits['title_max']} chars")
        
        # Clean and validate caption
        clean_caption = caption.strip()
        if len(clean_caption) > self.text_limits['caption_max']:
            clean_caption = clean_caption[:self.text_limits['caption_max']]
            issues.append(f"Caption truncated to {self.text_limits['caption_max']} chars")
        
        # Check for excessive emojis (more than 1 per 50 chars)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", 
            flags=re.UNICODE
        )
        
        emoji_count = len(emoji_pattern.findall(clean_caption))
        if emoji_count > len(clean_caption) / 50:
            issues.append(f"High emoji density: {emoji_count} emojis")
        
        # Clean and validate hashtags
        clean_hashtags = []
        seen_tags = set()
        
        for tag in hashtags:
            # Ensure hashtag format
            if not tag.startswith('#'):
                tag = f'#{tag}'
            
            # Remove invalid characters
            tag = re.sub(r'[^#\w]', '', tag)
            
            # Check for duplicates (case-insensitive)
            tag_lower = tag.lower()
            if tag_lower not in seen_tags and len(tag) > 1:
                clean_hashtags.append(tag)
                seen_tags.add(tag_lower)
        
        # Ensure hashtag count limits
        if len(clean_hashtags) > self.text_limits['hashtag_max']:
            clean_hashtags = clean_hashtags[:self.text_limits['hashtag_max']]
            issues.append(f"Hashtags limited to {self.text_limits['hashtag_max']}")
        elif len(clean_hashtags) < self.text_limits['hashtag_min']:
            # Add generic hashtags if too few
            generic_tags = ['#gaming', '#mobilegame', '#game', '#oyun', '#mobile']
            for tag in generic_tags:
                if tag.lower() not in seen_tags and len(clean_hashtags) < self.text_limits['hashtag_min']:
                    clean_hashtags.append(tag)
                    seen_tags.add(tag.lower())
            issues.append(f"Added generic hashtags to meet minimum of {self.text_limits['hashtag_min']}")
        
        # Check for banned/inappropriate content
        banned_patterns = [
            r'\b(spam|scam|hack|cheat|crack)\b',
            r'(http|https|www\.|bit\.ly)',  # URLs
            r'@\w{15,}',  # Suspicious mentions
        ]
        
        for pattern in banned_patterns:
            if re.search(pattern, clean_caption, re.IGNORECASE):
                issues.append(f"Potentially inappropriate content detected")
                break
        
        return {
            'title': clean_title,
            'caption': clean_caption,
            'hashtags': clean_hashtags,
            'issues': issues,
            'is_valid': len(issues) == 0,
            'metrics': {
                'title_length': len(clean_title),
                'caption_length': len(clean_caption),
                'hashtag_count': len(clean_hashtags),
                'emoji_count': emoji_count
            }
        }
    
    def check_quality(self, candidates: List[Dict], image_paths: List[str], 
                     output_base: str, utils_media) -> Dict:
        """
        Main quality control method.
        
        Args:
            candidates: List of content candidates
            image_paths: List of image paths to process
            output_base: Base output directory
            utils_media: Media utilities module
            
        Returns:
            Quality control results
        """
        try:
            logger.info("Starting quality control checks")
            
            # Process images
            images_output_dir = os.path.join(output_base, 'images')
            processed_images = self.process_images(
                image_paths[:10],  # Process up to 10 images
                images_output_dir,
                utils_media
            )
            
            # Validate and clean text content
            validated_candidates = []
            for i, candidate in enumerate(candidates):
                validation = self.validate_text(
                    candidate.get('title', ''),
                    candidate.get('caption', ''),
                    candidate.get('hashtags', [])
                )
                
                validated_candidates.append({
                    'original': candidate,
                    'validated': {
                        'title': validation['title'],
                        'caption': validation['caption'],
                        'hashtags': validation['hashtags']
                    },
                    'validation_issues': validation['issues'],
                    'metrics': validation['metrics'],
                    'is_valid': validation['is_valid']
                })
                
                logger.info(f"Validated candidate {i+1}: {len(validation['issues'])} issues")
            
            # Overall quality score
            total_issues = sum(len(vc['validation_issues']) for vc in validated_candidates)
            quality_score = max(0, 100 - (total_issues * 10))
            
            return {
                'status': 'success',
                'processed_images': {
                    'count': len(processed_images),
                    'paths': processed_images,
                    'output_dir': images_output_dir
                },
                'validated_candidates': validated_candidates,
                'quality_score': quality_score,
                'summary': f'Processed {len(processed_images)} images, validated {len(validated_candidates)} candidates, quality score: {quality_score}%'
            }
            
        except Exception as e:
            logger.error(f"Quality control failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'processed_images': {'count': 0, 'paths': [], 'output_dir': None},
                'validated_candidates': [],
                'quality_score': 0,
                'summary': f'Quality control failed: {str(e)}'
            }