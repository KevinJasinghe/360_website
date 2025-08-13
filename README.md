# Audio to Sheet Music Converter

A web application that converts audio and video files (or YouTube videos) to MIDI sheet music using AI.

## Features

- 📁 **File Upload**: Support for multiple audio/video formats (MP3, WAV, MP4, AVI, MOV, etc.)
- 📺 **YouTube Integration**: Direct download and processing from YouTube URLs
- 🧠 **AI Processing**: Converts audio to MIDI using machine learning
- 📊 **Progress Tracking**: Real-time processing status updates
- 📥 **Easy Download**: One-click MIDI file download

## Tech Stack

- **Frontend**: React.js with drag-and-drop file upload
- **Backend**: Flask with REST API
- **Audio Processing**: FFmpeg for format conversion
- **YouTube**: yt-dlp for video downloading
- **AI Model**: Custom Python implementation (placeholder included)
- **Deployment**: Docker with Render support

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- FFmpeg (for audio conversion)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd 360_website
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

3. **Set up the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Application: http://localhost:5000

### Render Deployment

1. **Connect your GitHub repository to Render**

2. **Create a Web Service with these settings**:
   - Build Command: `cd frontend && npm install && npm run build`
   - Start Command: `cd backend && python app.py`
   - Environment Variables:
     - `FLASK_ENV=production`
     - `MAX_CONTENT_LENGTH=52428800`

## API Endpoints

### File Upload
- `POST /api/upload` - Upload audio/video file
- `GET /api/upload/{id}` - Get upload information

### YouTube Processing
- `POST /api/youtube` - Submit YouTube URL for processing
- `POST /api/youtube/preview` - Preview YouTube video information
- `GET /api/youtube/{id}` - Get YouTube download status

### Processing
- `POST /api/process/{id}` - Start processing uploaded file or YouTube download
- `GET /api/process/{id}` - Get processing status and progress

### Download
- `GET /api/download/{id}` - Download generated MIDI file

### Utility
- `GET /health` - Health check endpoint
- `GET /api` - API information

## Supported Formats

### Input Formats
- **Audio**: MP3, WAV, M4A, FLAC, OGG, AAC
- **Video**: MP4, AVI, MOV, WebM, MKV
- **YouTube**: Any valid YouTube URL

### Output Format
- **MIDI**: Standard MIDI file (.mid)

## File Limits

- **Upload Size**: 50MB maximum
- **YouTube Videos**: 10 minutes maximum duration
- **Processing Time**: Typically 30 seconds to 2 minutes

## AI Model Integration

The application includes a placeholder AI processor in `backend/services/ai_processor.py`. To integrate your own AI model:

1. Replace the `process_audio_to_midi()` method with your actual implementation
2. Ensure your model accepts WAV files as input
3. Generate MIDI files as output
4. Update any dependencies in `requirements.txt`

## Project Structure

```
360_website/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── App.js           # Main app component
│   │   └── ...
│   ├── public/
│   └── package.json
├── backend/                 # Flask backend
│   ├── routes/             # API route handlers
│   ├── services/           # Business logic services
│   ├── uploads/            # Temporary file storage
│   ├── app.py              # Main Flask application
│   └── requirements.txt
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── README.md
```

## Development

### Adding New Features

1. **Backend**: Add new routes in `backend/routes/`
2. **Frontend**: Add new components in `frontend/src/components/`
3. **Services**: Add business logic in `backend/services/`

### Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Environment Variables

- `FLASK_ENV`: Set to 'production' for production deployment
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 50MB)
- `UPLOAD_FOLDER`: Directory for temporary file storage

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg on your system
2. **CORS errors**: Ensure CORS is properly configured in Flask
3. **File upload fails**: Check file size and format restrictions
4. **YouTube download fails**: Verify yt-dlp is installed and up to date

### Logs

- Backend logs are printed to console
- Check Docker logs: `docker-compose logs -f`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the GitHub repository.