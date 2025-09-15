"""Finalization Agent - Creates final package with optimized content."""

import os
import json
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import shutil

logger = logging.getLogger(__name__)


class FinalizationAgent:
    """Agent for finalizing and packaging content."""
    
    def __init__(self):
        """Initialize the finalization agent."""
        pass
    
    def rank_hashtags(self, hashtags: List[str], trend_data: Dict) -> List[str]:
        """
        Rank and order hashtags based on trend and niche balance.
        
        Args:
            hashtags: List of hashtags to rank
            trend_data: Trend analysis data
            
        Returns:
            Ordered list of hashtags
        """
        # Get trending hashtags from trend data
        trending_tags = set()
        if trend_data and 'hashtags' in trend_data:
            trending_tags = set(trend_data['hashtags'][:10])
        
        # Categorize hashtags
        trend_hashtags = []
        niche_hashtags = []
        brand_hashtags = []
        general_hashtags = []
        
        for tag in hashtags:
            tag_lower = tag.lower()
            
            # Check if trending
            if tag in trending_tags or any(t.lower() == tag_lower for t in trending_tags):
                trend_hashtags.append(tag)
            # Check for brand/game specific
            elif any(word in tag_lower for word in ['game', 'oyun', 'mobile', 'mobil']):
                brand_hashtags.append(tag)
            # Check for niche gaming
            elif any(word in tag_lower for word in ['rpg', 'mmo', 'pvp', 'fps', 'strategy']):
                niche_hashtags.append(tag)
            else:
                general_hashtags.append(tag)
        
        # Build ordered list: 3 trend + 2 niche + 2 brand + rest
        ordered = []
        
        # Add trending first
        ordered.extend(trend_hashtags[:3])
        
        # Add niche
        remaining_niche = [h for h in niche_hashtags if h not in ordered]
        ordered.extend(remaining_niche[:2])
        
        # Add brand/game
        remaining_brand = [h for h in brand_hashtags if h not in ordered]
        ordered.extend(remaining_brand[:2])
        
        # Fill with general
        remaining_general = [h for h in general_hashtags if h not in ordered]
        ordered.extend(remaining_general)
        
        # Add any remaining hashtags
        for tag in hashtags:
            if tag not in ordered:
                ordered.append(tag)
        
        return ordered[:12]  # Ensure max 12 hashtags
    
    def create_final_json(self, 
                         trend_results: Dict,
                         understanding_results: Dict,
                         generation_results: Dict,
                         quality_results: Dict,
                         output_path: str) -> str:
        """
        Create the final JSON output file.
        
        Args:
            trend_results: Trend analysis results
            understanding_results: Content understanding results
            generation_results: Content generation results
            quality_results: Quality control results
            output_path: Path to save the JSON file
            
        Returns:
            Path to created JSON file
        """
        try:
            # Extract validated candidates
            validated_candidates = quality_results.get('validated_candidates', [])
            
            # Create post options with ranked hashtags
            post_options = []
            for i, candidate in enumerate(validated_candidates):
                validated = candidate.get('validated', {})
                
                # Rank hashtags
                ranked_hashtags = self.rank_hashtags(
                    validated.get('hashtags', []),
                    trend_results
                )
                
                post_options.append({
                    'option_number': i + 1,
                    'title': validated.get('title', ''),
                    'caption': validated.get('caption', ''),
                    'hashtags': ranked_hashtags,
                    'metrics': candidate.get('metrics', {}),
                    'quality_notes': candidate.get('validation_issues', [])
                })
            
            # Create trend info summary
            trend_info = {
                'keywords_analyzed': trend_results.get('keywords_analyzed', 0),
                'top_trending': [
                    {
                        'keyword': kw['keyword'],
                        'score': round(kw['score'], 2)
                    }
                    for kw in trend_results.get('top_keywords', [])[:10]
                ],
                'recommended_hashtags': trend_results.get('hashtags', [])[:15]
            }
            
            # Create understanding brief
            understanding_brief = {
                'content_analyzed': {
                    'screenshots': understanding_results.get('screenshots', {}).get('count', 0),
                    'video_duration': understanding_results.get('video', {}).get('duration', 0),
                    'text_words': understanding_results.get('text', {}).get('word_count', 0)
                },
                'key_insights': {
                    'video_transcript_preview': understanding_results.get('video', {}).get('transcript', '')[:500],
                    'image_captions_sample': [
                        cap.get('caption', '') 
                        for cap in understanding_results.get('screenshots', {}).get('captions', [])[:3]
                    ],
                    'game_summary': understanding_results.get('text', {}).get('summary', '')[:300]
                }
            }
            
            # Get processed images info
            images_info = quality_results.get('processed_images', {})
            
            # Create final structure
            final_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'pipeline_version': '1.0.0',
                    'quality_score': quality_results.get('quality_score', 0)
                },
                'trend_info': trend_info,
                'understanding_brief': understanding_brief,
                'post_options': post_options,
                'assets': {
                    'images_dir': images_info.get('output_dir', ''),
                    'images_count': images_info.get('count', 0),
                    'image_files': [os.path.basename(p) for p in images_info.get('paths', [])]
                },
                'recommendations': {
                    'best_option': 1,  # Default to first option
                    'posting_time': 'Peak engagement hours: 19:00-22:00 TR time',
                    'engagement_tips': [
                        'Use the first 3 hashtags for maximum trend visibility',
                        'Post during evening hours for better engagement',
                        'Include a clear call-to-action in the caption',
                        'Use processed images for optimal Instagram display'
                    ]
                }
            }
            
            # Save JSON
            Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Created final JSON at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating final JSON: {e}")
            raise
    
    def create_package_zip(self, json_path: str, images_dir: str, output_path: str) -> str:
        """
        Create final package ZIP file.
        
        Args:
            json_path: Path to final JSON file
            images_dir: Directory containing processed images
            output_path: Path for output ZIP file
            
        Returns:
            Path to created ZIP file
        """
        try:
            Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add JSON file
                if os.path.exists(json_path):
                    zipf.write(json_path, 'final_post.json')
                    logger.info(f"Added JSON to package")
                
                # Add images
                if os.path.exists(images_dir):
                    image_count = 0
                    for root, dirs, files in os.walk(images_dir):
                        for file in files:
                            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                                file_path = os.path.join(root, file)
                                arc_name = os.path.join('images', file)
                                zipf.write(file_path, arc_name)
                                image_count += 1
                    logger.info(f"Added {image_count} images to package")
                
                # Add a README
                readme_content = """# Social Media Content Package

## Contents
- final_post.json: Complete post data with 3 content options
- images/: Processed images optimized for Instagram (1080x1350)

## Usage
1. Choose one of the 3 post options from final_post.json
2. Use the processed images from the images folder
3. Post during recommended hours for maximum engagement

## Post Options
Each option includes:
- Title (max 60 chars)
- Caption (max 2200 chars)
- 12 optimized hashtags

Generated with JoyCase1 Content Pipeline v1.0.0
"""
                zipf.writestr('README.md', readme_content)
            
            logger.info(f"Created package ZIP at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating package ZIP: {e}")
            raise
    
    def finalize(self,
                trend_results: Dict,
                understanding_results: Dict,
                generation_results: Dict,
                quality_results: Dict,
                output_base: str) -> Dict:
        """
        Main finalization method.
        
        Args:
            trend_results: Trend analysis results
            understanding_results: Content understanding results
            generation_results: Content generation results
            quality_results: Quality control results
            output_base: Base output directory
            
        Returns:
            Finalization results
        """
        try:
            logger.info("Starting finalization process")
            
            # Create final JSON
            json_path = os.path.join(output_base, 'final_post.json')
            final_json = self.create_final_json(
                trend_results,
                understanding_results,
                generation_results,
                quality_results,
                json_path
            )
            
            # Get images directory
            images_dir = quality_results.get('processed_images', {}).get('output_dir', '')
            
            # Create package ZIP
            zip_path = os.path.join(output_base, 'final_package.zip')
            package_zip = self.create_package_zip(
                final_json,
                images_dir,
                zip_path
            )
            
            # Calculate package size
            package_size = os.path.getsize(package_zip) if os.path.exists(package_zip) else 0
            
            return {
                'status': 'success',
                'final_json_path': final_json,
                'package_zip_path': package_zip,
                'package_size_mb': round(package_size / (1024 * 1024), 2),
                'outputs_directory': output_base,
                'summary': f'Successfully created final package with {quality_results.get("processed_images", {}).get("count", 0)} images and 3 post options'
            }
            
        except Exception as e:
            logger.error(f"Finalization failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'final_json_path': None,
                'package_zip_path': None,
                'outputs_directory': output_base,
                'summary': f'Finalization failed: {str(e)}'
            }