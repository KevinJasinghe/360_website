from flask import request, jsonify, current_app
from flask_restful import Resource
import os
import uuid
import threading
from services.youtube_downloader import YouTubeDownloader

class YouTubeDownloadResource(Resource):
    
    def post(self):
        try:
            data = request.get_json()
            
            if not data or 'url' not in data:
                return {'error': 'No URL provided'}, 400
            
            url = data['url'].strip()
            
            if not url:
                return {'error': 'Empty URL provided'}, 400
            
            # Validate YouTube URL
            if not YouTubeDownloader.is_valid_youtube_url(url):
                return {'error': 'Invalid YouTube URL'}, 400
            
            # Get video information
            video_info, error = YouTubeDownloader.get_video_info(url)
            if error:
                return {'error': f'Failed to get video info: {error}'}, 400
            
            # Check video duration (max 10 minutes = 600 seconds)
            if video_info['duration'] > 600:
                return {
                    'error': f'Video too long ({video_info["duration"]}s). Maximum allowed: 600s (10 minutes)'
                }, 400
            
            # Generate unique ID for this download
            download_id = str(uuid.uuid4())
            
            # Store download info in processing status
            from app import processing_status
            processing_status[download_id] = {
                'status': 'queued',
                'url': url,
                'video_info': video_info,
                'progress': 0,
                'message': 'Download queued',
                'type': 'youtube'
            }
            
            return {
                'download_id': download_id,
                'video_info': video_info,
                'message': 'YouTube download queued successfully'
            }, 200
            
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}, 500


class YouTubeInfoResource(Resource):
    
    def get(self, download_id):
        """Get information about a YouTube download"""
        try:
            from app import processing_status
            
            if download_id not in processing_status:
                return {'error': 'Download ID not found'}, 404
            
            download_info = processing_status[download_id]
            
            response = {
                'download_id': download_id,
                'status': download_info['status'],
                'message': download_info.get('message', ''),
                'progress': download_info.get('progress', 0),
                'video_info': download_info.get('video_info', {})
            }
            
            # Include file path if available
            if 'file_path' in download_info:
                response['file_path'] = download_info['file_path']
            
            return response, 200
            
        except Exception as e:
            return {'error': f'Failed to get download info: {str(e)}'}, 500


class YouTubePreviewResource(Resource):
    
    def post(self):
        """Get YouTube video information without downloading"""
        try:
            data = request.get_json()
            
            if not data or 'url' not in data:
                return {'error': 'No URL provided'}, 400
            
            url = data['url'].strip()
            
            if not YouTubeDownloader.is_valid_youtube_url(url):
                return {'error': 'Invalid YouTube URL'}, 400
            
            # Get video information
            video_info, error = YouTubeDownloader.get_video_info(url)
            if error:
                return {'error': f'Failed to get video info: {error}'}, 400
            
            # Check if video is too long
            is_too_long = video_info['duration'] > 600
            
            return {
                'video_info': video_info,
                'is_valid': not is_too_long,
                'max_duration': 600,
                'warning': 'Video is too long (max 10 minutes)' if is_too_long else None
            }, 200
            
        except Exception as e:
            return {'error': f'Preview failed: {str(e)}'}, 500