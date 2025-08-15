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
    
    # Configure Flask to use our custom static folder
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
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
    
    # Debug route to check static directory contents
    @app.route('/debug/static')
    def debug_static():
        """Debug endpoint to check static directory contents"""
        try:
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            contents = {}
            
            if os.path.exists(static_dir):
                contents['static_root'] = os.listdir(static_dir)
                
                # Check nested static directory
                nested_static = os.path.join(static_dir, 'static')
                if os.path.exists(nested_static):
                    contents['nested_static'] = os.listdir(nested_static)
                    
                    # Check CSS and JS directories
                    css_dir = os.path.join(nested_static, 'css')
                    js_dir = os.path.join(nested_static, 'js')
                    
                    if os.path.exists(css_dir):
                        contents['css_files'] = os.listdir(css_dir)
                    if os.path.exists(js_dir):
                        contents['js_files'] = os.listdir(js_dir)
            
            return jsonify({
                'static_dir': static_dir,
                'exists': os.path.exists(static_dir),
                'contents': contents
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Serve React frontend in both development and production
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        app.logger.info(f"🔍 Static file request: path='{path}'")
        
        # Calculate paths
        backend_dir = os.path.dirname(__file__)
        static_dir = os.path.join(backend_dir, 'static')
        app.logger.info(f"📁 Backend dir: {backend_dir}")
        app.logger.info(f"📁 Static dir: {static_dir}")
        app.logger.info(f"📁 Static dir exists: {os.path.exists(static_dir)}")
        
        if path != "":
            static_file_path = os.path.join(static_dir, path)
            app.logger.info(f"🔍 Looking for: {static_file_path}")
            app.logger.info(f"📂 File exists: {os.path.exists(static_file_path)}")
            
            # List contents of static directory for debugging
            if os.path.exists(static_dir):
                contents = os.listdir(static_dir)
                app.logger.info(f"📂 Static dir contents: {contents}")
                
                # If looking for static/css or static/js, check nested structure
                if path.startswith('static/'):
                    nested_path = os.path.join(static_dir, path)
                    app.logger.info(f"🔍 Nested path check: {nested_path}")
                    app.logger.info(f"📂 Nested exists: {os.path.exists(nested_path)}")
                    if os.path.exists(nested_path):
                        return send_from_directory(static_dir, path)
            
            if os.path.exists(static_file_path):
                app.logger.info(f"✅ Serving file: {static_file_path}")
                return send_from_directory(static_dir, path)
            else:
                app.logger.warning(f"❌ File not found: {static_file_path}")
        
        # Default to serving index.html for SPA routing
        index_path = os.path.join(static_dir, 'index.html')
        app.logger.info(f"📄 Serving index.html from: {index_path}")
        app.logger.info(f"📄 Index exists: {os.path.exists(index_path)}")
        
        if os.path.exists(index_path):
            return send_from_directory(static_dir, 'index.html')
        else:
            app.logger.error(f"❌ index.html not found at: {index_path}")
            return "Static files not configured", 500

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