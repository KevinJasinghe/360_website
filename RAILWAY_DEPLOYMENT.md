# Railway Deployment Guide

## Prerequisites
1. Railway account: https://railway.app/
2. GitHub account with your project repository
3. Model file in your repository

## Deployment Steps

### 1. Prepare Your Repository
```bash
# Make sure all Railway files are committed
git add railway.json Procfile nixpacks.toml requirements.txt .railwayignore
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 2. Deploy to Railway

1. **Login to Railway**: https://railway.app/
2. **New Project**: Click "New Project" 
3. **Deploy from GitHub**: Select your repository
4. **Branch**: Select `main` branch
5. **Auto-deploy**: Railway will automatically start building

### 3. Environment Variables
Set these in Railway dashboard under Variables:

```
FLASK_ENV=production
PORT=3001
MAX_CONTENT_LENGTH=209715200  # 200MB
MAX_AUDIO_DURATION=300        # 5 minutes
CLEANUP_INTERVAL=1800         # 30 minutes
```

### 4. Monitor Deployment

- **Logs**: Check Railway logs for deployment progress
- **Build Time**: Expect 5-10 minutes for first deployment
- **Memory Usage**: Monitor stays under 1GB

### 5. Test Deployment

Once deployed, test these endpoints:
- `GET /health` - Health check
- `GET /api` - API information
- `POST /api/upload` - File upload

## Optimization Notes

### Memory Optimizations Applied:
- CPU-only inference (no GPU)
- Reduced chunk size for long audio
- Limited PyTorch threads to 2
- Aggressive file cleanup (30 minutes)
- 200MB file size limit

### File Limits:
- Max file size: 200MB (vs 1GB locally)
- Max duration: 5 minutes (vs 10 minutes locally)
- Automatic cleanup: 30 minutes (vs 1 hour locally)

## Troubleshooting

### Out of Memory Errors:
- Reduce MAX_CONTENT_LENGTH further
- Reduce MAX_AUDIO_DURATION to 2-3 minutes
- Check Railway logs for memory usage spikes

### Model Loading Issues:
- Ensure model file is in repository
- Check MODEL_PATH environment variable
- Verify file size is under Railway limits

### Build Failures:
- Check requirements.txt for conflicting versions
- Review nixpacks.toml configuration
- Monitor build logs in Railway dashboard

## Production Ready Features:
✅ Health check endpoint
✅ Memory-optimized processing  
✅ Automatic file cleanup
✅ Error handling and logging
✅ CORS configured
✅ Production Flask config
✅ Environment-based configuration

## Next Steps:
1. Set up custom domain (optional)
2. Monitor performance and adjust limits
3. Consider database for processing status (Redis/PostgreSQL)
4. Set up monitoring and alerts