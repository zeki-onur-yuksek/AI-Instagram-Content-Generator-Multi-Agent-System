# JoyCase1 - Automated Content Generation Pipeline

An end-to-end automated content generation pipeline for social media that analyzes trends, understands multimedia content, generates engaging posts, ensures quality, and packages everything for deployment.

## 🚀 Features

- **Trend Analysis**: Analyzes keywords using PyTrends to identify trending topics
- **Content Understanding**: Processes videos (transcript + frames), images (BLIP captioning), and text
- **Content Generation**: Creates 3 post variations using OpenAI GPT-4 or fallback templates
- **Quality Control**: Validates text limits, processes images to Instagram format (1080x1350)
- **Final Packaging**: Creates JSON output and ZIP package with all assets

## 📋 Requirements

- Python 3.8+
- FFmpeg (for video processing)
- 4GB+ RAM recommended

## 🛠️ Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd joycase1

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install FFmpeg

**Windows:**
```bash
# Download from https://ffmpeg.org/download.html
# Add to PATH environment variable
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your credentials
# Required for Drive mode:
DRIVE_CREDS_JSON=./case1-471913-0b665a0fa244.json
DRIVE_FOLDER_ID=your_folder_id_here

# Optional (for better content generation):
OPENAI_API_KEY=your_openai_api_key_here
```

## 📁 Project Structure

```
joycase1/
├── app/
│   ├── main.py           # FastAPI endpoints
│   ├── controller.py      # Pipeline orchestration
│   ├── agents/           # Processing agents
│   │   ├── trend.py      # Trend analysis
│   │   ├── understand.py # Content understanding
│   │   ├── generate.py   # Content generation
│   │   ├── quality.py    # Quality control
│   │   └── finalize.py   # Final packaging
│   └── utils/            # Utilities
│       ├── media.py      # Video/image processing
│       └── drive.py      # Google Drive integration
├── outputs/              # Generated outputs (auto-created)
├── requirements.txt      # Python dependencies
├── .env                  # Environment configuration
└── README.md            # This file
```

## 🎮 Usage

### Start the Server

```bash
# Run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or directly with Python
python -m app.main
```

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
# Response: {"ok": true}
```

#### Run Pipeline - Local Mode

Prepare local files:
```
./Gameplay/         # Video files
./screenshot/       # Image files  
./asokeywords.txt   # Keywords (one per line or comma-separated)
./game.txt          # Game description
```

Run pipeline:
```bash
curl -X POST http://localhost:8000/run \
  -F "mode=local"
```

With custom paths:
```bash
curl -X POST http://localhost:8000/run \
  -F "mode=local" \
  -F "gameplay_dir=./my_videos" \
  -F "screenshot_dir=./my_images" \
  -F "aso_file=./keywords.txt" \
  -F "game_file=./description.txt"
```

#### Run Pipeline - Drive Mode

```bash
curl -X POST http://localhost:8000/run \
  -F "mode=drive" \
  -F "drive_creds_json=./case1-471913-0b665a0fa244.json" \
  -F "drive_folder_id=YOUR_FOLDER_ID"
```

### Expected Response

```json
{
  "status": "success",
  "final_post_json": "./outputs/run-20241212-143022/final_post.json",
  "package_zip": "./outputs/run-20241212-143022/final_package.zip",
  "outputs_dir": "./outputs/run-20241212-143022",
  "summary": "Pipeline completed successfully",
  "details": {
    "stages_completed": 6,
    "total_stages": 6,
    "timestamp": "20241212-143022"
  }
}
```

## 📦 Output Structure

### final_post.json
```json
{
  "metadata": {
    "generated_at": "2024-12-12T14:30:22",
    "quality_score": 85
  },
  "trend_info": {
    "top_trending": [...],
    "recommended_hashtags": [...]
  },
  "post_options": [
    {
      "option_number": 1,
      "title": "...",
      "caption": "...",
      "hashtags": ["#tag1", "#tag2", ...]
    },
    // 2 more options
  ],
  "assets": {
    "images_dir": "./outputs/run-../images",
    "image_files": ["processed_img1.jpg", ...]
  }
}
```

### final_package.zip
```
final_package.zip
├── final_post.json      # Complete post data
├── images/              # Processed images (1080x1350)
│   ├── processed_001.jpg
│   └── ...
└── README.md           # Usage instructions
```

## 🧪 Testing

### Quick Test with Sample Data

1. Create test files:
```bash
# Create directories
mkdir -p Gameplay screenshot

# Create sample text files
echo "mobile game, rpg, action, adventure, strategy" > asokeywords.txt
echo "This is an amazing mobile RPG game with stunning graphics." > game.txt

# Add sample images/videos to directories (optional)
```

2. Run test:
```bash
# Start server
uvicorn app.main:app --reload

# In another terminal, run pipeline
curl -X POST http://localhost:8000/run -F "mode=local"
```

3. Check outputs:
```bash
# List generated files
ls -la outputs/run-*/

# View final JSON
cat outputs/run-*/final_post.json

# Extract package
unzip -l outputs/run-*/final_package.zip
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DRIVE_CREDS_JSON` | Path to Google service account JSON | For Drive mode |
| `DRIVE_FOLDER_ID` | Google Drive folder ID | For Drive mode |
| `OPENAI_API_KEY` | OpenAI API key for content generation | Optional |
| `APP_ENV` | Environment (development/production) | Optional |
| `LOG_LEVEL` | Logging level (INFO/DEBUG/ERROR) | Optional |

### Fallback Behavior

- **No OpenAI Key**: Uses template-based content generation
- **No PyTrends Access**: Uses deterministic scoring based on keyword properties
- **No BLIP Model**: Returns placeholder captions
- **No FFmpeg**: Skips video processing

## 📊 Performance

- **Processing Time**: 30-60 seconds typical
- **Memory Usage**: 2-4 GB with models loaded
- **Output Size**: 5-20 MB depending on image count

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   # Verify installation
   ffmpeg -version
   ```

2. **Model download fails**
   ```bash
   # Pre-download models
   python -c "from transformers import BlipProcessor; BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base')"
   ```

3. **Drive authentication fails**
   - Verify service account has access to folder
   - Check credentials JSON is valid

4. **Out of memory**
   - Reduce max images/frames processed
   - Use CPU-only mode for models

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Pull requests are welcome! Please ensure:
- Code follows existing style
- Tests pass
- Documentation is updated