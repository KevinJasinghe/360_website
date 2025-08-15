# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a piano transcription web application that converts audio files (including YouTube videos) to MIDI sheet music using machine learning. The application consists of a React frontend and Flask backend with PyTorch-based AI model for audio-to-MIDI conversion.

## Development Commands

### Backend Development
```bash
cd backend
pip install -r requirements.txt
python app.py  # Development server
python app_production.py  # Production server
```

### Frontend Development
```bash
cd frontend
npm install
npm start  # Development server on port 3000
npm run build  # Production build
npm test  # Run tests
```

### Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Docker Development
```bash
docker-compose up --build  # Full application with both frontend and backend
```

## Architecture

### Backend Structure (Flask)
- **`app.py`** - Development Flask application
- **`app_production.py`** - Production Flask application with Railway optimizations
- **`config.py`** - Environment-specific configurations (Development/Production/Testing)
- **`routes/`** - API endpoints organized by functionality:
  - `upload.py` - File upload handling
  - `youtube.py` - YouTube video download and processing
  - `process.py` - AI processing and status tracking
- **`services/`** - Business logic services:
  - `ai_processor.py` - Main AI model interface for piano transcription
  - `audio_processor.py` - Audio file processing and conversion
  - `youtube_downloader.py` - YouTube video download using yt-dlp
  - `model_downloader.py` - Model downloading for Railway deployment
- **`models/`** - PyTorch model definitions:
  - `piano_transcription.py` - Piano transcription neural network model
- **`middleware/`** - Flask middleware:
  - `security.py` - Security headers and CORS configuration

### Frontend Structure (React)
- **`src/App.js`** - Main application component with routing
- **`src/components/`** - React components:
  - `FileUpload.js` - Drag-and-drop file upload interface
  - `YouTubeInput.js` - YouTube URL input and preview
  - `ProgressBar.js` - Processing progress visualization
  - `ResultDisplay.js` - Download results and MIDI playback

### AI Model Architecture
- Custom PyTorch model for piano transcription located in `backend/models/piano_transcription.py`
- Model weights stored in root directory: `model_training_model_epochs21_lr0.001_weight_decay0.0001_start20250814_165547_endongoing_epoch021.pth`
- Model automatically downloads if missing (Railway deployment)
- Processes WAV audio files and generates MIDI output

## Configuration Management

The application uses environment-specific configurations:
- **Development**: Uses local file storage, debug mode enabled
- **Production**: Railway-optimized with memory limits, logging, and ephemeral storage
- **Testing**: Minimal configuration for unit tests

Key environment variables:
- `FLASK_ENV` - Environment (development/production)
- `MODEL_PATH` - Path to PyTorch model file
- `MAX_CONTENT_LENGTH` - File upload size limit (200MB production, 1GB development)
- `MAX_AUDIO_DURATION` - Maximum audio processing duration
- `PORT` - Server port (Railway provides this)

## Processing Flow

1. **File Upload**: User uploads audio file or provides YouTube URL
2. **Audio Conversion**: FFmpeg converts to WAV format if needed
3. **AI Processing**: PyTorch model processes WAV file to generate MIDI
4. **Status Tracking**: Real-time progress updates via API polling
5. **Download**: Generated MIDI file available for download

## Deployment

### Railway Production
- Uses multi-stage Docker build optimized for Railway
- Model automatically downloads if not present
- Ephemeral storage with automatic cleanup
- Health checks and monitoring endpoints

### Local Docker
```bash
docker-compose up --build
# Exposes application on http://localhost:5000
```

## API Endpoints

- `POST /api/upload` - Upload audio file
- `POST /api/youtube` - Submit YouTube URL
- `POST /api/process/<id>` - Start AI processing
- `GET /api/process/<id>` - Get processing status
- `GET /api/download/<id>` - Download generated MIDI
- `GET /health` - Health check endpoint

## File Processing Limits

- **Development**: 1GB files, 10-minute audio duration
- **Production**: 200MB files, 5-minute audio duration
- Supported formats: MP3, WAV, MP4, AVI, MOV, WebM, YouTube URLs
- Output: Standard MIDI files (.mid)