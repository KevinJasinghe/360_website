from flask import request, jsonify, current_app, send_file
from flask_restful import Resource
import os
import uuid
import threading
from services.file_converter import FileConverter
from services.youtube_downloader import YouTubeDownloader
from services.ai_processor import AIProcessor
from services.audio_utils import AudioUtils

class ProcessResource(Resource):
    
    def get(self, process_id):
        """Get processing status"""
        try:
            from app import processing_status
            
            if process_id not in processing_status:
                return {'error': 'Process ID not found'}, 404
            
            process_info = processing_status[process_id]
            
            return {
                'process_id': process_id,
                'status': process_info['status'],
                'message': process_info.get('message', ''),
                'progress': process_info.get('progress', 0),
                'type': process_info.get('type', 'unknown'),
                'midi_ready': process_info.get('midi_ready', False)
            }, 200
            
        except Exception as e:
            return {'error': f'Failed to get process status: {str(e)}'}, 500
    
    def post(self, process_id):
        """Start processing uploaded file or YouTube download"""
        try:
            from app import processing_status
            
            if process_id not in processing_status:
                return {'error': 'Process ID not found'}, 404
            
            process_info = processing_status[process_id]
            
            if process_info['status'] in ['processing', 'completed']:
                return {
                    'message': f'Process already {process_info["status"]}',
                    'status': process_info['status']
                }, 200
            
            # Start processing in background thread with app context
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=self._process_file_background_with_context, 
                args=(app, process_id,)
            )
            thread.daemon = True
            thread.start()
            
            # Update status
            processing_status[process_id]['status'] = 'processing'
            processing_status[process_id]['message'] = 'Processing started'
            
            return {
                'message': 'Processing started',
                'process_id': process_id
            }, 200
            
        except Exception as e:
            return {'error': f'Failed to start processing: {str(e)}'}, 500
    
    def _process_file_background_with_context(self, app, process_id):
        """Background processing function with proper Flask context"""
        with app.app_context():
            try:
                from app import processing_status
                
                process_info = processing_status[process_id]
                
                # Handle YouTube downloads
                if process_info.get('type') == 'youtube':
                    file_path = self._handle_youtube_download(app, process_id, process_info)
                    if not file_path:
                        return  # Error already handled in _handle_youtube_download
                else:
                    # Get file path for regular uploads
                    file_path = process_info.get('file_path')
                    if not file_path or not os.path.exists(file_path):
                        self._update_progress(process_id, 0, "File not found", status='failed')
                        return
                
                # Step 1: Update progress
                self._update_progress(process_id, 30, "Processing with AI model...")
                
                # Step 2: Process with AI model directly (skip WAV conversion for now)
                midi_filename = f"{process_id}_output.mid"
                # Use absolute path to ensure file is saved correctly
                upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
                midi_path = os.path.join(upload_folder, midi_filename)
                print(f"🔧 Saving MIDI to: {midi_path}")
                
                # Use the AI processor directly
                print(f"🎵 Calling AI processor with file_path={file_path}, midi_path={midi_path}")
                ai_success, ai_message = AIProcessor.process_audio_to_midi(file_path, midi_path)
                print(f"🎼 AI processor result: success={ai_success}, message={ai_message}")
                print(f"📁 File exists after processing: {os.path.exists(midi_path)}")
                
                if ai_success:
                    # Success!
                    self._update_progress(process_id, 100, "Processing completed successfully!", status='completed')
                    
                    # Store MIDI file info
                    processing_status[process_id]['midi_path'] = midi_path
                    processing_status[process_id]['midi_filename'] = midi_filename
                    processing_status[process_id]['midi_ready'] = True
                else:
                    # Failed
                    self._update_progress(process_id, 0, f"AI processing failed: {ai_message}", status='failed')
                    
            except Exception as e:
                self._update_progress(process_id, 0, f"Processing error: {str(e)}", status='failed')
    
    def _handle_youtube_download(self, app, process_id, process_info):
        """Handle YouTube video download and return audio file path"""
        try:
            self._update_progress(process_id, 10, "Downloading YouTube video...")
            
            url = process_info.get('url')
            if not url:
                self._update_progress(process_id, 0, "No YouTube URL found", status='failed')
                return None
            
            # Generate unique filename for the download
            video_id = process_info.get('video_info', {}).get('video_id', 'unknown')
            audio_filename = f"{process_id}_{video_id}.wav"
            upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
            audio_path = os.path.join(upload_folder, audio_filename)
            
            self._update_progress(process_id, 20, "Downloading audio from YouTube...")
            
            # Download using YouTubeDownloader
            success, message = YouTubeDownloader.download_audio(url, audio_path)
            
            if success:
                self._update_progress(process_id, 25, "YouTube download completed")
                
                # Find the actual downloaded file (could be .webm, .m4a, etc.)
                base_path = audio_path.replace('.wav', '')
                possible_files = [
                    f"{base_path}.webm",
                    f"{base_path}.m4a", 
                    f"{base_path}.mp4",
                    f"{base_path}.opus",
                    audio_path  # Original .wav
                ]
                
                actual_file = None
                for possible_file in possible_files:
                    if os.path.exists(possible_file):
                        actual_file = possible_file
                        break
                
                if actual_file:
                    print(f"✅ Found downloaded file: {actual_file}")
                    return actual_file
                else:
                    self._update_progress(process_id, 0, "Downloaded file not found", status='failed')
                    return None
            else:
                self._update_progress(process_id, 0, f"YouTube download failed: {message}", status='failed')
                return None
                
        except Exception as e:
            self._update_progress(process_id, 0, f"YouTube download error: {str(e)}", status='failed')
            return None
    
    def _update_progress(self, process_id, progress, message, status=None):
        """Update processing progress"""
        try:
            from app import processing_status
            
            if process_id in processing_status:
                processing_status[process_id]['progress'] = progress
                processing_status[process_id]['message'] = message
                if status:
                    processing_status[process_id]['status'] = status
                    
        except Exception:
            pass  # Don't fail the main process if progress update fails


class DownloadResource(Resource):
    
    def get(self, process_id):
        """Download the generated MIDI file"""
        try:
            from app import processing_status
            
            if process_id not in processing_status:
                return {'error': 'Process ID not found'}, 404
            
            process_info = processing_status[process_id]
            
            if process_info.get('status') != 'completed':
                return {'error': 'Processing not completed yet'}, 400
            
            if not process_info.get('midi_ready', False):
                return {'error': 'MIDI file not ready'}, 400
            
            midi_path = process_info.get('midi_path')
            if not midi_path or not os.path.exists(midi_path):
                return {'error': 'MIDI file not found'}, 404
            
            # Generate download filename
            original_name = process_info.get('original_filename', 'audio')
            base_name = os.path.splitext(original_name)[0]
            download_name = f"{base_name}_sheet_music.mid"
            
            return send_file(
                midi_path,
                as_attachment=True,
                download_name=download_name,
                mimetype='audio/midi'
            )
            
        except Exception as e:
            return {'error': f'Download failed: {str(e)}'}, 500