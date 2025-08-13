from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_restful import Api
import os
import uuid
import threading
import time

# Import route resources
from routes.upload import FileUploadResource, FileInfoResource
from routes.youtube import YouTubeDownloadResource, YouTubeInfoResource, YouTubePreviewResource
from routes.process import ProcessResource, DownloadResource

# Import AI processor
from services.ai_processor import AIProcessor

app = Flask(__name__)
CORS(app)
api = Api(app)

UPLOAD_FOLDER = '../uploads'
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create model weights directory
WEIGHTS_FOLDER = 'weights'
os.makedirs(WEIGHTS_FOLDER, exist_ok=True)

# Initialize AI model
print("🔧 Initializing AI model...")
model_path = os.path.join(WEIGHTS_FOLDER, 'piano_transcription_weights.pth')
if AIProcessor.initialize(model_path if os.path.exists(model_path) else None):
    model_info = AIProcessor.get_model_info()
    print(f"✅ AI model ready: {model_info['model_name']} on {model_info['device']}")
    print(f"   Parameters: {model_info['num_parameters']:,}, Size: {model_info['model_size_mb']:.1f}MB")
else:
    print("❌ AI model initialization failed - using fallback mode")

# In-memory storage for processing status (in production, use Redis or database)
processing_status = {}

def cleanup_old_files():
    """Clean up files older than 1 hour"""
    while True:
        try:
            current_time = time.time()
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > 3600:  # 1 hour
                        os.remove(file_path)
                        print(f"Cleaned up old file: {filename}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        time.sleep(300)  # Check every 5 minutes

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

# Register API routes
api.add_resource(FileUploadResource, '/api/upload')
api.add_resource(FileInfoResource, '/api/upload/<string:upload_id>')
api.add_resource(YouTubeDownloadResource, '/api/youtube')
api.add_resource(YouTubeInfoResource, '/api/youtube/<string:download_id>')
api.add_resource(YouTubePreviewResource, '/api/youtube/preview')
api.add_resource(ProcessResource, '/api/process/<string:process_id>')
api.add_resource(DownloadResource, '/api/download/<string:process_id>')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    else:
        return send_from_directory('static', 'index.html')

# API info endpoint
@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        'message': 'Audio to Sheet Music API',
        'endpoints': {
            'upload': '/api/upload',
            'youtube': '/api/youtube',
            'process': '/api/process/<id>',
            'download': '/api/download/<id>',
            'health': '/health'
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3001)