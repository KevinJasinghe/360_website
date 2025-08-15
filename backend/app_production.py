"""
Production-safe Flask application for Piano Transcription
"""
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_restful import Api
import os
import uuid
import threading
import time
import logging
from config import config

# Import route resources
from routes.upload import FileUploadResource, FileInfoResource
from routes.youtube import YouTubeDownloadResource, YouTubeInfoResource, YouTubePreviewResource
from routes.process import ProcessResource, DownloadResource

# Import AI processor
from services.ai_processor import AIProcessor

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize CORS with configuration
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize Flask-RESTful
    api = Api(app)
    
    # Initialize AI model
    init_ai_model(app)
    
    # Setup cleanup thread
    if not app.config.get('TESTING'):
        setup_cleanup_thread(app)
    
    # Register API routes
    register_routes(api)
    
    # Register general routes
    register_general_routes(app)
    
    return app

def init_ai_model(app):
    """Initialize AI model safely with download support for Railway"""
    with app.app_context():
        try:
            app.logger.info("Initializing AI model...")
            
            # Try to download model if not available (for Railway deployment)
            from services.model_downloader import EnvironmentModelDownloader
            
            model_available = EnvironmentModelDownloader.ensure_model_available()
            
            if model_available:
                model_path = EnvironmentModelDownloader.get_model_path()
                app.logger.info(f"Using model: {model_path}")
            else:
                # Fallback to configured path
                model_path = app.config['MODEL_PATH']
                app.logger.warning("Model download failed, trying configured path")
            
            if os.path.exists(model_path):
                success = AIProcessor.initialize(model_path)
            else:
                app.logger.warning(f"Model file not found: {model_path}")
                success = AIProcessor.initialize(None)
            
            if success:
                model_info = AIProcessor.get_model_info()
                app.logger.info(f"AI model ready: {model_info['model_name']} on {model_info['device']}")
                app.logger.info(f"Parameters: {model_info['num_parameters']:,}, Size: {model_info['model_size_mb']:.1f}MB")
            else:
                app.logger.error("AI model initialization failed - using fallback mode")
                
        except Exception as e:
            app.logger.error(f"AI model initialization error: {e}")

def setup_cleanup_thread(app):
    """Setup file cleanup thread"""
    def cleanup_old_files():
        """Clean up files older than configured interval"""
        with app.app_context():
            while True:
                try:
                    current_time = time.time()
                    upload_folder = app.config['UPLOAD_FOLDER']
                    cleanup_interval = app.config['CLEANUP_INTERVAL']
                    
                    if os.path.exists(upload_folder):
                        for filename in os.listdir(upload_folder):
                            file_path = os.path.join(upload_folder, filename)
                            if os.path.isfile(file_path):
                                file_age = current_time - os.path.getctime(file_path)
                                if file_age > cleanup_interval:
                                    os.remove(file_path)
                                    app.logger.info(f"Cleaned up old file: {filename}")
                except Exception as e:
                    app.logger.error(f"Error during cleanup: {e}")
                time.sleep(300)  # Check every 5 minutes
    
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()

def register_routes(api):
    """Register API routes"""
    api.add_resource(FileUploadResource, '/api/upload')
    api.add_resource(FileInfoResource, '/api/upload/<string:upload_id>')
    api.add_resource(YouTubeDownloadResource, '/api/youtube')
    api.add_resource(YouTubeInfoResource, '/api/youtube/<string:download_id>')
    api.add_resource(YouTubePreviewResource, '/api/youtube/preview')
    api.add_resource(ProcessResource, '/api/process/<string:process_id>')
    api.add_resource(DownloadResource, '/api/download/<string:process_id>')

def register_general_routes(app):
    """Register general Flask routes"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Check if AI model is available
            ai_status = AIProcessor.is_initialized()
            
            # Check disk space (basic check)
            upload_folder = app.config['UPLOAD_FOLDER']
            disk_available = os.path.exists(upload_folder)
            
            status = {
                'status': 'healthy' if ai_status and disk_available else 'degraded',
                'ai_model': 'ready' if ai_status else 'not_ready',
                'storage': 'available' if disk_available else 'unavailable',
                'version': '1.0.0'
            }
            
            return jsonify(status), 200 if status['status'] == 'healthy' else 503
            
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
    
    @app.route('/api', methods=['GET'])
    def api_info():
        """API information endpoint"""
        return jsonify({
            'message': 'Piano Transcription API',
            'version': '1.0.0',
            'endpoints': {
                'upload': '/api/upload',
                'youtube': '/api/youtube',
                'process': '/api/process/<id>',
                'download': '/api/download/<id>',
                'health': '/health'
            },
            'limits': {
                'max_file_size_mb': app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024),
                'max_duration_seconds': app.config['MAX_AUDIO_DURATION']
            }
        })
    
    # Only serve static files in development
    if app.config['DEBUG']:
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve(path):
            if path and os.path.exists(os.path.join('static', path)):
                return send_from_directory('static', path)
            else:
                return send_from_directory('static', 'index.html')
    else:
        # Serve a simple frontend in production
        @app.route('/')
        def index():
            return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Piano Transcription API</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6;
            background: #f5f5f5;
        }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c5282; margin-bottom: 30px; }
        .api-section { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .endpoint { font-family: monospace; background: #e2e8f0; padding: 5px 10px; border-radius: 4px; }
        .method { font-weight: bold; color: #2d3748; }
        .upload-form { margin: 20px 0; padding: 20px; background: #ebf8ff; border-radius: 8px; }
        input[type="file"] { margin: 10px 0; }
        button { background: #3182ce; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #2c5282; }
        .status { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .success { background: #c6f6d5; color: #22543d; }
        .error { background: #fed7d7; color: #742a2a; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎹 Piano Transcription API</h1>
        <p>Convert audio files to MIDI using AI-powered piano transcription.</p>
        
        <div class="api-section">
            <h3>📡 API Endpoints</h3>
            <p><span class="method">POST</span> <span class="endpoint">/api/upload</span> - Upload audio file</p>
            <p><span class="method">POST</span> <span class="endpoint">/api/youtube</span> - Process YouTube URL</p>
            <p><span class="method">POST</span> <span class="endpoint">/api/process/{id}</span> - Start transcription</p>
            <p><span class="method">GET</span> <span class="endpoint">/api/process/{id}</span> - Check progress</p>
            <p><span class="method">GET</span> <span class="endpoint">/api/download/{id}</span> - Download MIDI</p>
            <p><span class="method">GET</span> <span class="endpoint">/health</span> - System status</p>
        </div>
        
        <div class="upload-form">
            <h3>🎵 Quick Upload Test</h3>
            <form id="uploadForm" enctype="multipart/form-data">
                <div>
                    <label for="audioFile">Select audio file (MP3, WAV, etc.):</label><br>
                    <input type="file" id="audioFile" name="file" accept="audio/*" required>
                </div>
                <div>
                    <button type="submit">Upload & Transcribe</button>
                </div>
            </form>
            <div id="status"></div>
        </div>
        
        <div class="api-section">
            <h3>ℹ️ System Information</h3>
            <p><strong>Version:</strong> 1.0.0</p>
            <p><strong>Max File Size:</strong> 200MB</p>
            <p><strong>Max Duration:</strong> 5 minutes</p>
            <p><strong>Supported Formats:</strong> MP3, WAV, MP4, AVI, MOV, WebM</p>
        </div>
    </div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const statusDiv = document.getElementById('status');
            const fileInput = document.getElementById('audioFile');
            const file = fileInput.files[0];
            
            if (!file) {
                statusDiv.innerHTML = '<div class="status error">Please select a file</div>';
                return;
            }
            
            try {
                statusDiv.innerHTML = '<div class="status">Uploading...</div>';
                
                const formData = new FormData();
                formData.append('file', file);
                
                const uploadResponse = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (!uploadResponse.ok) throw new Error('Upload failed');
                const uploadData = await uploadResponse.json();
                
                statusDiv.innerHTML = '<div class="status success">✅ Upload successful! Starting transcription...</div>';
                
                // Start processing
                const processResponse = await fetch(`/api/process/${uploadData.id}`, {
                    method: 'POST'
                });
                
                if (!processResponse.ok) throw new Error('Processing failed');
                const processData = await processResponse.json();
                
                statusDiv.innerHTML = `<div class="status success">🎵 Transcription started! Task ID: ${uploadData.id}</div>`;
                
                // Poll for completion
                const pollStatus = async () => {
                    try {
                        const statusResponse = await fetch(`/api/process/${uploadData.id}`);
                        const statusData = await statusResponse.json();
                        
                        if (statusData.status === 'completed') {
                            statusDiv.innerHTML = `
                                <div class="status success">
                                    ✅ Transcription complete! 
                                    <a href="/api/download/${uploadData.id}" download>Download MIDI</a>
                                </div>
                            `;
                        } else if (statusData.status === 'failed') {
                            statusDiv.innerHTML = `<div class="status error">❌ Transcription failed: ${statusData.error}</div>`;
                        } else {
                            statusDiv.innerHTML = `<div class="status">Processing... ${statusData.progress || 0}%</div>`;
                            setTimeout(pollStatus, 2000);
                        }
                    } catch (error) {
                        statusDiv.innerHTML = `<div class="status error">❌ Error checking status: ${error.message}</div>`;
                    }
                };
                
                setTimeout(pollStatus, 2000);
                
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">❌ Error: ${error.message}</div>`;
            }
        });
    </script>
</body>
</html>'''

# Global processing status storage
# In production, this should be replaced with Redis or a database
processing_status = {}

# Create the application
app = create_app()

if __name__ == '__main__':
    # Railway provides PORT environment variable
    port = int(os.environ.get('PORT', app.config.get('PORT', 3001)))
    host = os.environ.get('HOST', app.config.get('HOST', '0.0.0.0'))
    debug = app.config.get('DEBUG', False)
    
    app.logger.info(f"Starting Piano Transcription API on {host}:{port}")
    app.run(debug=debug, host=host, port=port, threaded=True)