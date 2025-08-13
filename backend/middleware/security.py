"""
Security middleware for Flask application
"""
from functools import wraps
from flask import request, jsonify, current_app
import time
import hashlib
from collections import defaultdict

# Rate limiting storage (in production, use Redis)
request_counts = defaultdict(list)

def rate_limit(max_requests=10, per_seconds=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if client_ip is None:
                client_ip = 'unknown'
            
            # Clean old requests
            now = time.time()
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip] 
                if now - req_time < per_seconds
            ]
            
            # Check rate limit
            if len(request_counts[client_ip]) >= max_requests:
                current_app.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {per_seconds} seconds'
                }), 429
            
            # Record this request
            request_counts[client_ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_file_upload(allowed_extensions=None, max_size=None):
    """File upload validation decorator"""
    if allowed_extensions is None:
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Check file extension
            if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                return jsonify({
                    'error': 'Invalid file type',
                    'allowed': list(allowed_extensions)
                }), 400
            
            # Check file size if specified
            if max_size:
                file.seek(0, 2)  # Seek to end
                size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if size > max_size:
                    return jsonify({
                        'error': 'File too large',
                        'max_size_mb': max_size // (1024 * 1024)
                    }), 413
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal attacks"""
    import os
    import re
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100-len(ext)] + ext
    
    # Ensure it's not empty or dangerous
    if not filename or filename.startswith('.'):
        filename = 'upload_' + filename
    
    return filename

def validate_youtube_url(url):
    """Validate YouTube URL to prevent SSRF attacks"""
    import re
    
    if not url or not isinstance(url, str):
        return False
    
    # Only allow YouTube URLs
    youtube_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(www\.)?youtu\.be/[\w-]+',
        r'^https?://(www\.)?youtube\.com/embed/[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    return False

class SecurityHeaders:
    """Add security headers to all responses"""
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.after_request(self.add_security_headers)
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "media-src 'none'; "
            "object-src 'none'; "
            "frame-src 'none';"
        )
        
        return response