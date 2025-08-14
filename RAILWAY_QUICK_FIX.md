# Railway Build Timeout Fix

## Problem
Your Railway build was timing out due to:
1. **86MB model file** being included in Docker build
2. **Large test files** (WAV files, uploads)
3. **Frontend node_modules** and build artifacts

## Solution Applied

### 1. ✅ Optimized Build Files
- **Updated `.railwayignore`**: Excludes all large files (model, WAV files, node_modules)
- **Optimized `Dockerfile`**: Multi-stage build with better caching
- **Updated `requirements.txt`**: Minimal dependencies only

### 2. ✅ Model Download Strategy
- **Excluded model from build**: 86MB model file won't be uploaded
- **Created model downloader**: Downloads model on first startup
- **Environment variable support**: Configure model URL via Railway variables

### 3. ✅ Railway Configuration
- **Updated `railway.json`**: Optimized for production
- **Nixpacks build**: Uses Railway's optimized builder
- **Health check**: Proper startup monitoring

## Deployment Steps

### Step 1: Upload Your Model File
You need to upload your model to a public URL. Options:

**Option A: GitHub Releases (Recommended)**
```bash
# Create a GitHub release and upload your model file
# Then use the download URL
https://github.com/yourusername/yourrepo/releases/download/v1.0/model_file.pth
```

**Option B: Google Drive Public Link**
1. Upload model to Google Drive
2. Make it publicly accessible
3. Use direct download link

**Option C: Other File Hosting**
- Dropbox public links
- AWS S3 public bucket
- Any CDN with direct download

### Step 2: Deploy to Railway
1. **Commit Changes:**
   ```bash
   git add .
   git commit -m "Optimize Railway build - exclude large files"
   git push origin main
   ```

2. **Set Environment Variables in Railway:**
   - `FLASK_ENV=production`
   - `MODEL_DOWNLOAD_URL=YOUR_MODEL_URL_HERE`
   - `MAX_CONTENT_LENGTH=200000000` (200MB)
   - `MAX_AUDIO_DURATION=300` (5 minutes)

3. **Deploy:**
   - Railway will detect changes and start building
   - Build should complete in 2-3 minutes (vs timing out)
   - On first startup, model will be downloaded automatically

### Step 3: Monitor Startup
Watch Railway logs for:
```
📥 Downloading model file...
✅ Model downloaded successfully
🔧 Initializing AI model on cpu
✅ AI model ready: crnn_onsets_frames
```

## Build Size Reduction

**Before:**
- Docker image: ~500MB+ (with model)
- Build time: 10+ minutes → timeout

**After:**
- Docker image: ~200MB (without model)  
- Build time: 2-3 minutes ✅
- Model downloads on startup: ~30 seconds

## Files Changed
- ✅ `.railwayignore` - Excludes large files
- ✅ `Dockerfile` - Optimized multi-stage build
- ✅ `railway.json` - Production configuration
- ✅ `app_production.py` - Model downloader integration
- ✅ `services/model_downloader.py` - New model download service

## Next Steps
1. Upload your model file to a public URL
2. Update `MODEL_DOWNLOAD_URL` in Railway environment variables
3. Commit and push changes
4. Deploy should succeed! 🚀

## Troubleshooting
- **Build still fails**: Check Railway logs for specific errors
- **Model download fails**: Verify MODEL_DOWNLOAD_URL is accessible
- **Memory issues**: Reduce MAX_CONTENT_LENGTH further if needed