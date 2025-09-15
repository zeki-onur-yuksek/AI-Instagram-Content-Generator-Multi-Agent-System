"""Simple test script to verify the application setup."""

import os
import sys
import json
from PIL import Image
import numpy as np

def create_test_image():
    """Create a simple test image for testing."""
    # Create a simple gradient image
    width, height = 800, 600
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create gradient
    for y in range(height):
        for x in range(width):
            img_array[y, x] = [
                int(255 * x / width),  # Red gradient
                int(255 * y / height),  # Green gradient
                128  # Fixed blue
            ]
    
    # Save image
    img = Image.fromarray(img_array)
    os.makedirs('screenshot', exist_ok=True)
    img.save('screenshot/test_image.jpg')
    print("✓ Created test image: screenshot/test_image.jpg")

def test_imports():
    """Test if all modules can be imported."""
    try:
        from app.controller import ContentPipelineController
        print("✓ Controller imported successfully")
        
        from app.agents import (
            TrendAnalysisAgent,
            ContentUnderstandingAgent,
            ContentGenerationAgent,
            QualityControlAgent,
            FinalizationAgent
        )
        print("✓ All agents imported successfully")
        
        from app.utils import media, drive
        print("✓ Utilities imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_file_structure():
    """Test if required files and directories exist."""
    required_files = [
        'asokeywords.txt',
        'game.txt',
        '.env',
        'requirements.txt',
        'app/main.py',
        'app/controller.py'
    ]
    
    required_dirs = [
        'Gameplay',
        'screenshot',
        'app/agents',
        'app/utils'
    ]
    
    all_good = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ File exists: {file}")
        else:
            print(f"✗ File missing: {file}")
            all_good = False
    
    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"✓ Directory exists: {dir}")
        else:
            print(f"✗ Directory missing: {dir}")
            all_good = False
    
    return all_good

def main():
    """Run all tests."""
    print("=" * 50)
    print("JoyCase1 Application Test")
    print("=" * 50)
    
    print("\n1. Testing file structure...")
    structure_ok = test_file_structure()
    
    print("\n2. Creating test data...")
    create_test_image()
    
    print("\n3. Testing imports...")
    imports_ok = test_imports()
    
    print("\n" + "=" * 50)
    if structure_ok and imports_ok:
        print("✓ All tests passed! Application is ready.")
        print("\nTo start the server, run:")
        print("  python -m uvicorn app.main:app --reload")
        print("\nThen test with:")
        print("  curl -X POST http://localhost:8000/run -F 'mode=local'")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    print("=" * 50)

if __name__ == "__main__":
    main()