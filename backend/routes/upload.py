from flask import request, jsonify, current_app
from flask_restful import Resource
import os
import uuid
import threading
from werkzeug.utils import secure_filename
from services.audio_utils import AudioUtils
from services.file_converter import FileConverter

class FileUploadResource(Resource):
    
    def post(self):
        try:
            # Check if file is present
            if 'file' not in request.files:
                return {'error': 'No file provided'}, 400
            
            file = request.files['file']
            
            if file.filename == '':
                return {'error': 'No file selected'}, 400
            
            # Validate file type
            is_valid, message = AudioUtils.validate_file_type(file)
            if not is_valid:
                return {'error': message}, 400
            
            # Generate unique ID for this upload
            upload_id = str(uuid.uuid4())
            
            # Create secure filename
            original_filename = file.filename
            secure_name = AudioUtils.secure_and_unique_filename(original_filename, upload_id)
            
            # Save file
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_name)
            file.save(upload_path)
            
            # Store upload info in processing status
            from app import processing_status
            processing_status[upload_id] = {
                'status': 'uploaded',
                'original_filename': original_filename,
                'file_path': upload_path,
                'file_size': os.path.getsize(upload_path),
                'progress': 0,
                'message': 'File uploaded successfully',
                'type': 'upload'
            }
            
            return {
                'upload_id': upload_id,
                'filename': original_filename,
                'size': processing_status[upload_id]['file_size'],
                'size_formatted': AudioUtils.format_file_size(processing_status[upload_id]['file_size']),
                'message': 'File uploaded successfully'
            }, 200
            
        except Exception as e:
            return {'error': f'Upload failed: {str(e)}'}, 500


class FileInfoResource(Resource):
    
    def get(self, upload_id):
        """Get information about an uploaded file"""
        try:
            from app import processing_status
            
            if upload_id not in processing_status:
                return {'error': 'Upload ID not found'}, 404
            
            upload_info = processing_status[upload_id]
            file_path = upload_info.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                return {'error': 'File not found'}, 404
            
            # Get audio/video information if possible
            audio_info, error = FileConverter.get_audio_info(file_path)
            
            response = {
                'upload_id': upload_id,
                'status': upload_info['status'],
                'original_filename': upload_info['original_filename'],
                'file_size': upload_info['file_size'],
                'size_formatted': AudioUtils.format_file_size(upload_info['file_size']),
                'message': upload_info.get('message', ''),
                'progress': upload_info.get('progress', 0)
            }
            
            if audio_info:
                response['audio_info'] = audio_info
            elif error:
                response['audio_error'] = error
            
            return response, 200
            
        except Exception as e:
            return {'error': f'Failed to get file info: {str(e)}'}, 500