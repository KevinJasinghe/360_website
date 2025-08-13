# Audio/Video to Sheet Music Conversion Website - Implementation Plan

## Overview
A web application that accepts audio/video files OR YouTube video links, converts them to WAV format, processes them through an AI model to generate sheet music, and returns MIDI files for download.

## Tech Stack
- **Frontend**: React.js
- **Backend**: Flask + Flask-RESTful
- **File Processing**: FFmpeg (for format conversion)
- **YouTube Download**: yt-dlp (for downloading YouTube videos)
- **AI Processing**: Python (converted from your Jupyter notebook)
- **Deployment**: Render
- **Storage**: Local file system (temporary)

## Project Structure
```
360_website/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.js
│   │   │   ├── YouTubeInput.js
│   │   │   ├── ProgressBar.js
│   │   │   └── ResultDisplay.js
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── public/
├── backend/
│   ├── app.py
│   ├── routes/
│   │   ├── upload.py
│   │   ├── youtube.py
│   │   └── process.py
│   ├── services/
│   │   ├── file_converter.py
│   │   ├── youtube_downloader.py
│   │   ├── ai_processor.py
│   │   └── audio_utils.py
│   ├── requirements.txt
│   └── uploads/ (temporary storage)
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Implementation Steps

### Phase 1: Backend Setup
1. **Flask Application Setup**
   - Create Flask app with CORS enabled
   - Set up file upload endpoint with 50MB limit
   - Configure temporary file storage

2. **File Processing Service**
   - Install FFmpeg for audio conversion
   - Install yt-dlp for YouTube video downloading
   - Create converter service to handle multiple formats → WAV
   - Create YouTube downloader service
   - Implement file validation and cleanup

3. **AI Integration**
   - Convert your Jupyter notebook code into a Python service
   - Create processing endpoint that accepts WAV files
   - Return MIDI file generation

### Phase 2: Frontend Development
1. **React Application Setup**
   - Create file upload component with drag & drop
   - Create YouTube link input component
   - Implement file type validation on client side
   - Add progress tracking UI

2. **User Interface**
   - Clean, minimalist design
   - Tabbed interface: "Upload File" and "YouTube Link"
   - File upload area with format support display
   - YouTube URL input field with validation
   - Progress bar during processing
   - Download button for completed MIDI files

### Phase 3: Integration & Testing
1. **API Integration**
   - Connect frontend to Flask API
   - Handle file uploads with progress tracking
   - Implement error handling and user feedback

2. **Testing**
   - Test with various audio/video formats
   - Performance testing with different file sizes
   - Error handling for unsupported formats

### Phase 4: Deployment
1. **Dockerization**
   - Create Docker container with FFmpeg
   - Set up environment for Python dependencies
   - Configure for Render deployment

2. **Production Setup**
   - Environment variables for configuration
   - Logging and monitoring
   - File cleanup automation

## API Endpoints

### POST /api/upload
- Accept file upload
- Validate format and size (max 50MB)
- Return upload ID for tracking

### POST /api/youtube
- Accept YouTube URL
- Validate URL format
- Return download ID for tracking

### GET /api/process/{process_id}
- Start YouTube download (if needed) and conversion to WAV
- Process through AI model
- Return processing status and progress

### GET /api/download/{process_id}
- Download generated MIDI file
- Clean up temporary files

## File Processing Pipeline

### File Upload Path:
1. **Upload** → Validate format and size
2. **Convert** → FFmpeg conversion to WAV (if needed)
3. **Process** → AI model processes WAV → generates MIDI
4. **Serve** → Return MIDI file for download
5. **Cleanup** → Remove temporary files

### YouTube URL Path:
1. **URL Input** → Validate YouTube URL format
2. **Download** → yt-dlp downloads video as audio
3. **Convert** → FFmpeg conversion to WAV
4. **Process** → AI model processes WAV → generates MIDI
5. **Serve** → Return MIDI file for download
6. **Cleanup** → Remove temporary files

## Technical Considerations

### File Handling
- 50MB file size limit for uploads
- YouTube video length limit: 10 minutes (to prevent long processing times)
- Supported formats: MP4, MP3, WAV, AVI, MOV, M4A, FLAC, OGG
- YouTube URL validation (youtube.com, youtu.be domains)
- Temporary storage with automatic cleanup after 1 hour

### Performance
- Asynchronous processing for better UX
- Progress updates via polling (can upgrade to WebSockets later)
- File compression for faster uploads

### Security
- File type validation on both client and server
- YouTube URL validation and sanitization
- Sanitized file names
- No permanent storage of user files
- Rate limiting on uploads and YouTube downloads
- Content-Length checks for YouTube downloads

### Deployment (Render)
- Use Docker for consistent environment with FFmpeg and yt-dlp
- Environment variables for configuration
- Automatic cleanup of old files
- Logging for debugging
- Handle yt-dlp updates for YouTube compatibility

## Development Timeline
- **Week 1**: Backend setup and file processing
- **Week 2**: AI integration and testing
- **Week 3**: Frontend development
- **Week 4**: Integration, testing, and deployment

## Next Steps
1. Set up project structure
2. Create Flask backend with file upload and YouTube endpoints
3. Install and configure FFmpeg and yt-dlp
4. Convert Jupyter notebook to Flask service
5. Build React frontend with tabbed interface
6. Test integration (both file upload and YouTube)
7. Deploy to Render

## Future Enhancements (Optional)
- Real-time progress via WebSockets
- Multiple output formats (PDF sheet music)
- Audio preview of generated MIDI
- Batch processing
- User feedback system