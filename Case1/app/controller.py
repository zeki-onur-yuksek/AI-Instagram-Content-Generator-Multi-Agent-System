"""Main controller for orchestrating the content pipeline."""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.agents.trend import TrendAnalysisAgent
from app.agents.understand import ContentUnderstandingAgent
from app.agents.generate import ContentGenerationAgent
from app.agents.quality import QualityControlAgent
from app.agents.finalize import FinalizationAgent
from app.utils import media, drive

logger = logging.getLogger(__name__)


class ContentPipelineController:
    """Controller for managing the entire content generation pipeline."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the pipeline controller.
        
        Args:
            openai_api_key: Optional OpenAI API key
        """
        self.openai_api_key = openai_api_key
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all pipeline agents."""
        try:
            self.agents['trend'] = TrendAnalysisAgent()
            self.agents['understand'] = ContentUnderstandingAgent()
            self.agents['generate'] = ContentGenerationAgent(self.openai_api_key)
            self.agents['quality'] = QualityControlAgent()
            self.agents['finalize'] = FinalizationAgent()
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise
    
    def prepare_inputs(self, mode: str, **kwargs) -> Dict:
        """
        Prepare input files based on mode (local or drive).
        
        Args:
            mode: 'local' or 'drive'
            **kwargs: Additional parameters for input preparation
            
        Returns:
            Dictionary with input file paths
        """
        if mode == 'drive':
            # Prepare from Google Drive
            creds_path = kwargs.get('drive_creds_json') or os.getenv('DRIVE_CREDS_JSON')
            folder_id = kwargs.get('drive_folder_id') or os.getenv('DRIVE_FOLDER_ID')
            
            if not creds_path or not folder_id:
                raise ValueError("Drive credentials and folder ID required for drive mode")
            
            return drive.prepare_inputs_from_drive(creds_path, folder_id)
        else:
            # Prepare from local files
            return drive.prepare_local_inputs(
                gameplay_dir=kwargs.get('gameplay_dir'),
                screenshot_dir=kwargs.get('screenshot_dir'),
                aso_file=kwargs.get('aso_file'),
                game_file=kwargs.get('game_file')
            )
    
    def run_pipeline(self, mode: str = 'local', **kwargs) -> Dict:
        """
        Run the complete content generation pipeline.
        
        Args:
            mode: 'local' or 'drive'
            **kwargs: Additional parameters
            
        Returns:
            Pipeline execution results
        """
        # Create output directory with timestamp
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        output_base = os.path.join('./outputs', f'run-{timestamp}')
        Path(output_base).mkdir(parents=True, exist_ok=True)
        
        results = {
            'status': 'started',
            'output_directory': output_base,
            'timestamp': timestamp,
            'mode': mode,
            'stages': {}
        }
        
        try:
            # Stage 1: Prepare inputs
            logger.info(f"Stage 1: Preparing inputs (mode: {mode})")
            inputs = self.prepare_inputs(mode, **kwargs)
            results['stages']['input_preparation'] = {
                'status': 'success',
                'inputs': inputs
            }
            
            # Stage 2: Trend Analysis
            logger.info("Stage 2: Running trend analysis")
            trend_results = self.agents['trend'].analyze(
                inputs.get('aso_file', './asokeywords.txt')
            )
            results['stages']['trend_analysis'] = trend_results
            
            # Stage 3: Content Understanding
            logger.info("Stage 3: Running content understanding")
            understanding_results = self.agents['understand'].analyze(
                inputs, 
                media
            )
            results['stages']['content_understanding'] = understanding_results
            
            # Stage 4: Content Generation
            logger.info("Stage 4: Running content generation")
            generation_results = self.agents['generate'].generate(
                trend_results,
                understanding_results
            )
            results['stages']['content_generation'] = generation_results
            
            # Stage 5: Quality Control
            logger.info("Stage 5: Running quality control")
            
            # Collect image paths for processing
            image_paths = []
            
            # Get screenshot paths
            screenshot_dir = inputs.get('screenshot_dir')
            if screenshot_dir and os.path.exists(screenshot_dir):
                for file in os.listdir(screenshot_dir):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        image_paths.append(os.path.join(screenshot_dir, file))
            
            # Get sample images from understanding results if available
            if 'full_data' in understanding_results:
                screenshot_data = understanding_results['full_data'].get('all_screenshot_captions', [])
                for item in screenshot_data:
                    if item.get('path') and os.path.exists(item['path']):
                        if item['path'] not in image_paths:
                            image_paths.append(item['path'])
            
            quality_results = self.agents['quality'].check_quality(
                generation_results.get('candidates', []),
                image_paths,
                output_base,
                media
            )
            results['stages']['quality_control'] = quality_results
            
            # Stage 6: Finalization
            logger.info("Stage 6: Running finalization")
            finalization_results = self.agents['finalize'].finalize(
                trend_results,
                understanding_results,
                generation_results,
                quality_results,
                output_base
            )
            results['stages']['finalization'] = finalization_results
            
            # Update overall status
            results['status'] = 'completed'
            results['final_outputs'] = {
                'json_path': finalization_results.get('final_json_path'),
                'package_path': finalization_results.get('package_zip_path'),
                'outputs_directory': output_base
            }
            
            logger.info(f"Pipeline completed successfully. Outputs in: {output_base}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def get_pipeline_status(self) -> Dict:
        """
        Get current pipeline status.
        
        Returns:
            Status information
        """
        return {
            'agents_loaded': list(self.agents.keys()),
            'ready': len(self.agents) == 5,
            'has_openai': bool(self.openai_api_key)
        }