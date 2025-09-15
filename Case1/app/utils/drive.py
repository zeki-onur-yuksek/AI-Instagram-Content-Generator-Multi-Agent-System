"""Google Drive integration utilities."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

logger = logging.getLogger(__name__)


class DriveManager:
    """Manage Google Drive operations with service account."""
    
    def __init__(self, credentials_path: str, folder_id: str):
        """
        Initialize Drive manager with service account credentials.
        
        Args:
            credentials_path: Path to service account JSON file
            folder_id: Google Drive folder ID to work with
        """
        self.credentials_path = credentials_path
        self.folder_id = folder_id
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Drive service with service account."""
        try:
            # Load service account credentials
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            # Build service
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Google Drive service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            raise
    
    def list_folder_contents(self) -> List[Dict]:
        """
        List all files and folders in the specified folder.
        
        Returns:
            List of file/folder metadata dictionaries
        """
        try:
            query = f"'{self.folder_id}' in parents"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size)",
                pageSize=100
            ).execute()
            
            items = results.get('files', [])
            logger.info(f"Found {len(items)} items in Drive folder")
            return items
            
        except Exception as e:
            logger.error(f"Error listing folder contents: {e}")
            return []
    
    def download_file(self, file_id: str, output_path: str) -> bool:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            output_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)
            
            fh = io.FileIO(output_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            logger.info(f"Downloaded file to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            return False
    
    def download_folder_contents(self, local_base_path: str) -> Dict[str, List[str]]:
        """
        Download all contents from the Drive folder to local directory.
        
        Args:
            local_base_path: Base path for local storage
            
        Returns:
            Dictionary with paths to downloaded content by type
        """
        downloaded = {
            'gameplay': [],
            'screenshots': [],
            'text_files': []
        }
        
        try:
            items = self.list_folder_contents()
            
            for item in items:
                name = item['name']
                file_id = item['id']
                mime_type = item['mimeType']
                
                # Determine local path based on file type
                if mime_type == 'application/vnd.google-apps.folder':
                    # Handle folders
                    if 'gameplay' in name.lower():
                        folder_path = os.path.join(local_base_path, 'Gameplay')
                        self._download_folder_files(file_id, folder_path, 'gameplay', downloaded)
                    elif 'screenshot' in name.lower():
                        folder_path = os.path.join(local_base_path, 'screenshot')
                        self._download_folder_files(file_id, folder_path, 'screenshots', downloaded)
                else:
                    # Handle individual files
                    local_path = os.path.join(local_base_path, name)
                    if self.download_file(file_id, local_path):
                        if name.endswith('.txt'):
                            downloaded['text_files'].append(local_path)
                        elif any(ext in name.lower() for ext in ['.mp4', '.avi', '.mov']):
                            downloaded['gameplay'].append(local_path)
                        elif any(ext in name.lower() for ext in ['.jpg', '.png', '.jpeg']):
                            downloaded['screenshots'].append(local_path)
            
            logger.info(f"Downloaded content summary: {len(downloaded['gameplay'])} videos, "
                       f"{len(downloaded['screenshots'])} images, {len(downloaded['text_files'])} text files")
            return downloaded
            
        except Exception as e:
            logger.error(f"Error downloading folder contents: {e}")
            return downloaded
    
    def _download_folder_files(self, folder_id: str, local_folder: str, 
                               category: str, downloaded: Dict):
        """Download files from a subfolder."""
        try:
            query = f"'{folder_id}' in parents"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=100
            ).execute()
            
            items = results.get('files', [])
            Path(local_folder).mkdir(parents=True, exist_ok=True)
            
            for item in items:
                if item['mimeType'] != 'application/vnd.google-apps.folder':
                    local_path = os.path.join(local_folder, item['name'])
                    if self.download_file(item['id'], local_path):
                        downloaded[category].append(local_path)
                        
        except Exception as e:
            logger.error(f"Error downloading folder files: {e}")


def prepare_inputs_from_drive(
    credentials_path: str,
    folder_id: str,
    local_base_path: str = "./temp_drive_data"
) -> Dict[str, any]:
    """
    Download and prepare inputs from Google Drive.
    
    Args:
        credentials_path: Path to service account credentials
        folder_id: Google Drive folder ID
        local_base_path: Local directory to store downloaded files
        
    Returns:
        Dictionary with paths to input files
    """
    try:
        manager = DriveManager(credentials_path, folder_id)
        downloaded = manager.download_folder_contents(local_base_path)
        
        # Find specific files
        inputs = {
            'gameplay_dir': os.path.join(local_base_path, 'Gameplay'),
            'screenshot_dir': os.path.join(local_base_path, 'screenshot'),
            'aso_file': None,
            'game_file': None
        }
        
        # Look for text files
        for text_file in downloaded['text_files']:
            if 'asokeywords' in os.path.basename(text_file).lower():
                inputs['aso_file'] = text_file
            elif 'game.txt' in os.path.basename(text_file).lower():
                inputs['game_file'] = text_file
        
        # Fallback to default locations if not found
        if not inputs['aso_file']:
            default_aso = os.path.join(local_base_path, 'asokeywords.txt')
            if os.path.exists(default_aso):
                inputs['aso_file'] = default_aso
        
        if not inputs['game_file']:
            default_game = os.path.join(local_base_path, 'game.txt')
            if os.path.exists(default_game):
                inputs['game_file'] = default_game
        
        logger.info(f"Prepared Drive inputs: {inputs}")
        return inputs
        
    except Exception as e:
        logger.error(f"Error preparing Drive inputs: {e}")
        raise


def prepare_local_inputs(
    gameplay_dir: Optional[str] = None,
    screenshot_dir: Optional[str] = None,
    aso_file: Optional[str] = None,
    game_file: Optional[str] = None
) -> Dict[str, str]:
    """
    Prepare local input paths with defaults.
    
    Args:
        gameplay_dir: Path to gameplay videos directory
        screenshot_dir: Path to screenshots directory
        aso_file: Path to ASO keywords file
        game_file: Path to game description file
        
    Returns:
        Dictionary with validated input paths
    """
    # Use defaults if not provided
    inputs = {
        'gameplay_dir': gameplay_dir or './Gameplay',
        'screenshot_dir': screenshot_dir or './screenshot',
        'aso_file': aso_file or './asokeywords.txt',
        'game_file': game_file or './game.txt'
    }
    
    # Validate paths exist
    for key, path in inputs.items():
        if not os.path.exists(path):
            logger.warning(f"Path does not exist: {path}")
            # Create empty file/directory for testing
            if key.endswith('_dir'):
                Path(path).mkdir(parents=True, exist_ok=True)
            else:
                Path(path).touch(exist_ok=True)
    
    logger.info(f"Prepared local inputs: {inputs}")
    return inputs