from flask import jsonify, send_file, request
from flask_restful import Resource
import os
from pathlib import Path

from services.sheet_music_generator import (
    SheetMusicGenerator, 
    validate_midi_for_sheet_music, 
    get_supported_sheet_formats
)


class SheetMusicResource(Resource):
    """Convert MIDI files to sheet music"""
    
    def post(self, process_id):
        """
        Convert MIDI to sheet music
        
        Expected JSON body:
        {
            "format": "musicxml" | "png"  # optional, defaults to musicxml
        }
        """
        try:
            # Check if sheet music generation is available
            if not SheetMusicGenerator.is_available():
                return {
                    'error': 'Sheet music generation not available',
                    'message': 'music21 library required for sheet music conversion'
                }, 503
            
            # Find the MIDI file for this process
            uploads_dir = '../uploads'
            midi_files = []
            
            # Look for MIDI files with this process ID
            for filename in os.listdir(uploads_dir):
                if process_id in filename and filename.endswith(('.mid', '.midi')):
                    midi_files.append(os.path.join(uploads_dir, filename))
            
            if not midi_files:
                return {
                    'error': 'MIDI file not found',
                    'message': f'No MIDI file found for process ID: {process_id}'
                }, 404
            
            # Use the first MIDI file found
            midi_file_path = midi_files[0]
            
            # Validate MIDI file
            is_valid, validation_msg = validate_midi_for_sheet_music(midi_file_path)
            if not is_valid:
                return {
                    'error': 'Invalid MIDI file',
                    'message': validation_msg
                }, 400
            
            # Get format from request
            data = request.get_json() or {}
            output_format = data.get('format', 'musicxml').lower()
            
            if output_format not in get_supported_sheet_formats():
                return {
                    'error': 'Unsupported format',
                    'message': f'Supported formats: {get_supported_sheet_formats()}'
                }, 400
            
            # Generate sheet music
            if output_format == 'musicxml':
                success, output_path, message = SheetMusicGenerator.midi_to_musicxml(midi_file_path)
            elif output_format == 'png':
                success, output_path, message = SheetMusicGenerator.midi_to_png(midi_file_path)
            else:
                return {
                    'error': 'Unsupported format',
                    'message': f'Format {output_format} not supported'
                }, 400
            
            if success and output_path:
                file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                return {
                    'success': True,
                    'message': message,
                    'sheet_music_id': process_id,
                    'format': output_format,
                    'file_size': file_size,
                    'download_url': f'/api/sheet-music/download/{process_id}?format={output_format}'
                }
            else:
                return {
                    'error': 'Sheet music generation failed',
                    'message': message
                }, 500
                
        except Exception as e:
            return {
                'error': 'Sheet music generation error',
                'message': str(e)
            }, 500


class SheetMusicDownloadResource(Resource):
    """Download generated sheet music files"""
    
    def get(self, process_id):
        """Download sheet music file"""
        try:
            # Get format from query parameter
            output_format = request.args.get('format', 'musicxml').lower()
            
            # Find the sheet music file
            uploads_dir = '../uploads'
            
            # Look for sheet music files with this process ID
            if output_format == 'musicxml':
                file_extensions = ['_sheet.xml', '.xml']
            elif output_format == 'png':
                file_extensions = ['_sheet.png', '.png']
            else:
                return {
                    'error': 'Unsupported format',
                    'message': f'Format {output_format} not supported'
                }, 400
            
            sheet_file_path = None
            for filename in os.listdir(uploads_dir):
                if process_id in filename:
                    for ext in file_extensions:
                        if filename.endswith(ext):
                            sheet_file_path = os.path.join(uploads_dir, filename)
                            break
                    if sheet_file_path:
                        break
            
            if not sheet_file_path or not os.path.exists(sheet_file_path):
                return {
                    'error': 'Sheet music file not found',
                    'message': f'No sheet music file found for process ID: {process_id}'
                }, 404
            
            # Determine MIME type and filename
            if output_format == 'musicxml':
                mimetype = 'application/vnd.recordare.musicxml+xml'
                as_attachment_name = f'{process_id}_sheet_music.xml'
            elif output_format == 'png':
                mimetype = 'image/png'
                as_attachment_name = f'{process_id}_sheet_music.png'
            else:
                mimetype = 'application/octet-stream'
                as_attachment_name = f'{process_id}_sheet_music'
            
            return send_file(
                sheet_file_path,
                as_attachment=True,
                download_name=as_attachment_name,
                mimetype=mimetype
            )
            
        except Exception as e:
            return {
                'error': 'Sheet music download error',
                'message': str(e)
            }, 500


class SheetMusicInfoResource(Resource):
    """Get information about available sheet music formats and capabilities"""
    
    def get(self):
        """Get sheet music generation information"""
        return {
            'available': SheetMusicGenerator.is_available(),
            'supported_formats': get_supported_sheet_formats(),
            'capabilities': {
                'midi_to_musicxml': True,
                'midi_to_png': 'png' in get_supported_sheet_formats(),
                'score_analysis': True,
                'note_quantization': True,
                'tempo_detection': True
            },
            'requirements': {
                'music21': 'Required for all sheet music operations',
                'musescore': 'Optional for PNG export (if available)'
            }
        }


class SheetMusicTestResource(Resource):
    """Test sheet music generation with a sample file"""
    
    def post(self):
        """Create test sheet music to verify functionality"""
        try:
            if not SheetMusicGenerator.is_available():
                return {
                    'error': 'Sheet music generation not available',
                    'message': 'music21 library required'
                }, 503
            
            # Create test sheet music
            test_path = os.path.join('../uploads', 'test_sheet_music.xml')
            success, message = SheetMusicGenerator.create_test_sheet_music(test_path)
            
            if success:
                file_size = os.path.getsize(test_path) if os.path.exists(test_path) else 0
                return {
                    'success': True,
                    'message': message,
                    'test_file': test_path,
                    'file_size': file_size
                }
            else:
                return {
                    'error': 'Test creation failed',
                    'message': message
                }, 500
                
        except Exception as e:
            return {
                'error': 'Test error',
                'message': str(e)
            }, 500