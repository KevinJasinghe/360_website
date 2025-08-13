# Piano Transcription - Production Deployment Guide

## 🚀 Render Deployment

### Prerequisites
- Render account (free tier available)
- GitHub repository with your code
- Model weights file (optional - will use random weights if not provided)

### Quick Deploy to Render

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Production-ready deployment"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `piano-transcription-api`
     - **Environment**: `Python`
     - **Build Command**: `pip install -r backend/requirements_production.txt`
     - **Start Command**: `cd backend && gunicorn --bind 0.0.0.0:$PORT app_production:app`
     - **Instance Type**: `Free` (or `Starter` for better performance)

3. **Set Environment Variables**
   ```bash
   FLASK_ENV=production
   MAX_CONTENT_LENGTH=52428800  # 50MB
   MAX_AUDIO_DURATION=300      # 5 minutes
   MAX_YOUTUBE_DURATION=300    # 5 minutes
   CORS_ORIGINS=*              # Update with your frontend URL
   ```

### Alternative: Docker Deployment

1. **Build the Docker image**
   ```bash
   cd backend
   docker build -t piano-transcription .
   ```

2. **Run the container**
   ```bash
   docker run -p 3001:3001 \
     -e FLASK_ENV=production \
     -e MAX_CONTENT_LENGTH=52428800 \
     piano-transcription
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Flask environment |
| `PORT` | `3001` | Server port |
| `MAX_CONTENT_LENGTH` | `52428800` | Max file size (50MB) |
| `MAX_AUDIO_DURATION` | `300` | Max audio length (5 min) |
| `MAX_YOUTUBE_DURATION` | `300` | Max YouTube video length |
| `UPLOAD_FOLDER` | `/tmp/uploads` | Upload directory |
| `CLEANUP_INTERVAL` | `1800` | File cleanup interval (30 min) |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `SECRET_KEY` | auto-generated | Flask secret key |

### Production Settings

- **File Size Limit**: 50MB (reduced from 1GB)
- **Duration Limit**: 5 minutes (reduced from 10 minutes)
- **Rate Limiting**: 10 requests per minute per IP
- **File Cleanup**: Automatic cleanup every 30 minutes
- **Security Headers**: CSP, HSTS, XSS protection
- **Logging**: Structured logging to files

## 🛡️ Security Features

### File Upload Security
- File type validation (audio formats only)
- File size limits
- Filename sanitization
- Path traversal prevention

### YouTube Download Security
- URL validation (YouTube domains only)
- Duration limits
- File size limits (100MB)
- Timeout protection (30s)

### General Security
- Rate limiting (10 req/min per IP)
- Security headers (CSP, HSTS, etc.)
- Non-root Docker user
- Input validation
- Error handling without info disclosure

## 📊 Monitoring

### Health Check Endpoint
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "ai_model": "ready",
  "storage": "available",
  "version": "1.0.0"
}
```

### API Information
```bash
GET /api
```

### Logging
- Application logs: `/app/logs/piano_transcription.log`
- Health checks: Available via `/health`
- Error tracking: Structured logging

## 🔄 Model Deployment

### Option 1: Include in Build
1. Place `piano_transcription_weights.pth` in `backend/weights/`
2. Update `.dockerignore` to include the weights
3. Rebuild and deploy

### Option 2: External Storage
1. Upload model to cloud storage (S3, Google Cloud, etc.)
2. Download during container startup
3. Set `MODEL_PATH` environment variable

### Option 3: No Model (Testing)
- App will use random weights for testing
- Still processes audio but transcription quality will be poor

## 🚨 Production Recommendations

### For High Traffic
1. **Upgrade to Paid Plan**: Render Starter ($7/month) or Professional ($25/month)
2. **Use Redis**: Replace in-memory rate limiting with Redis
3. **Add Database**: Store processing status in PostgreSQL
4. **CDN**: Use CloudFlare for static assets
5. **Load Balancer**: Multiple instances for high availability

### For Better Performance
1. **GPU Support**: Deploy on platforms with GPU support for faster inference
2. **Caching**: Cache model outputs for repeated requests
3. **Async Processing**: Use Celery with Redis for background processing
4. **File Storage**: Use S3 for file uploads instead of ephemeral storage

### Security Hardening
1. **API Keys**: Add API key authentication
2. **User Accounts**: Add user registration/login
3. **Usage Quotas**: Per-user rate limiting
4. **Audit Logging**: Track all API usage
5. **SSL Certificates**: Use HTTPS (automatic on Render)

## 🐛 Troubleshooting

### Common Issues

1. **Build Failure**
   - Check Python version (3.11 required)
   - Verify requirements.txt dependencies
   - Check for missing system packages (ffmpeg)

2. **Memory Issues**
   - Reduce batch size in model processing
   - Lower file size limits
   - Use smaller model if available

3. **Audio Processing Errors**
   - Ensure ffmpeg is installed
   - Check file format support
   - Verify librosa installation

4. **YouTube Download Fails**
   - Update yt-dlp to latest version
   - Check YouTube API changes
   - Verify URL format

### Logs Access
```bash
# Render logs
render logs <service-name>

# Docker logs
docker logs <container-id>
```

## 📞 Support

For deployment issues:
1. Check the health endpoint: `/health`
2. Review application logs
3. Verify environment variables
4. Test with smaller files first

Production deployment is now ready! 🎉