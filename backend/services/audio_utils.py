import os
import mimetypes
from werkzeug.utils import secure_filename

class AudioUtils:
    
    ALLOWED_EXTENSIONS = {
        'mp3', 'wav', 'mp4', 'avi', 'mov', 'm4a', 
        'flac', 'ogg', 'webm', 'mkv', 'aac'
    }
    
    AUDIO_MIME_TYPES = {
        'audio/mpeg', 'audio/wav', 'audio/wave', 'audio/x-wav',
        'audio/mp4', 'audio/m4a', 'audio/flac', 'audio/ogg',
        'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo',
        'video/webm', 'video/x-matroska'
    }
    
    @staticmethod
    def allowed_file(filename):
        """Check if the file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in AudioUtils.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_type(file):
        """Validate file type by extension and MIME type"""
        if not file or not file.filename:
            return False, "No file selected"
        
        filename = file.filename.lower()
        
        # Check extension
        if not AudioUtils.allowed_file(filename):
            return False, "File type not supported"
        
        # Check MIME type if available
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and mime_type not in AudioUtils.AUDIO_MIME_TYPES:
            return False, "Invalid file type"
        
        return True, "File type valid"
    
    @staticmethod
    def secure_and_unique_filename(filename, upload_id):
        """Generate a secure and unique filename"""
        # Secure the original filename
        secured = secure_filename(filename)
        
        # Get file extension
        if '.' in secured:
            name, ext = secured.rsplit('.', 1)
            ext = ext.lower()
        else:
            name = secured
            ext = ''
        
        # Create unique filename with upload ID
        if ext:
            unique_filename = f"{upload_id}_{name}.{ext}"
        else:
            unique_filename = f"{upload_id}_{name}"
        
        return unique_filename
    
    @staticmethod
    def get_file_info(file_path):
        """Get basic file information"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'size': stat.st_size,
                'mime_type': mime_type,
                'created': stat.st_ctime,
                'modified': stat.st_mtime
            }
        except Exception:
            return None
    
    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def is_audio_file(filename):
        """Check if file is primarily an audio file"""
        audio_extensions = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac'}
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return ext in audio_extensions
    
    @staticmethod
    def is_video_file(filename):
        """Check if file is primarily a video file"""
        video_extensions = {'mp4', 'avi', 'mov', 'webm', 'mkv'}
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return ext in video_extensions