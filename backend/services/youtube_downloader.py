import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs

class YouTubeDownloader:
    
    @staticmethod
    def is_valid_youtube_url(url):
        """Validate if the URL is a valid YouTube URL"""
        youtube_patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)',
            r'youtube\.com\/.*[?&]v=',
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    @staticmethod
    def extract_video_id(url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def get_video_info(url):
        """Get video information without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                duration = info.get('duration', 0)
                title = info.get('title', 'Unknown')
                
                return {
                    'title': title,
                    'duration': duration,
                    'video_id': info.get('id'),
                    'uploader': info.get('uploader', 'Unknown')
                }, None
                
        except Exception as e:
            return None, f"Error getting video info: {str(e)}"
    
    @staticmethod
    def download_audio(url, output_path, max_duration=600):  # 10 minutes max
        """Download audio from YouTube video with security checks"""
        try:
            # Validate URL format first
            if not YouTubeDownloader.is_valid_youtube_url(url):
                return False, "Invalid YouTube URL format"
            
            # Get video info first to check duration
            info, error = YouTubeDownloader.get_video_info(url)
            if error:
                return False, error
            
            # Security: Check duration limits
            if info['duration'] > max_duration:
                return False, f"Video too long ({info['duration']}s). Maximum allowed: {max_duration}s"
            
            # Security: Validate output path to prevent directory traversal
            import os
            output_path = os.path.abspath(output_path)
            # Allow uploads directory and /tmp directory
            allowed_paths = ['/tmp/', os.getcwd(), os.path.abspath('../uploads'), os.path.abspath('./uploads')]
            path_allowed = any(output_path.startswith(allowed_path) for allowed_path in allowed_paths)
            
            if not path_allowed:
                print(f"❌ Path validation failed: {output_path}")
                print(f"   Allowed paths: {allowed_paths}")
                return False, "Invalid output path"
            
            # Download options - use webm/opus format that librosa can handle
            ydl_opts = {
                'format': 'bestaudio[ext=webm]/bestaudio/best[filesize<100M]',  # Max 100MB
                'outtmpl': output_path.replace('.wav', '.%(ext)s'),
                'noplaylist': True,
                'quiet': False,  # Enable logging for debugging
                'no_warnings': False,
                'extract_flat': False,
                'socket_timeout': 30,
                'retries': 3,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Check if file was actually downloaded
            base_path = output_path.replace('.wav', '')
            possible_files = [
                f"{base_path}.webm",
                f"{base_path}.m4a", 
                f"{base_path}.mp4",
                f"{base_path}.opus",
                output_path
            ]
            
            downloaded_file = None
            for possible_file in possible_files:
                if os.path.exists(possible_file):
                    downloaded_file = possible_file
                    break
            
            if downloaded_file:
                return True, f"Download successful: {downloaded_file}"
            else:
                return False, "Download completed but file not found"
            
        except yt_dlp.DownloadError as e:
            # Check if download actually succeeded despite the error
            base_path = output_path.replace('.wav', '')
            possible_files = [f"{base_path}.webm", f"{base_path}.m4a", f"{base_path}.mp4", f"{base_path}.opus", output_path]
            
            for possible_file in possible_files:
                if os.path.exists(possible_file):
                    return True, f"Download successful despite error: {possible_file}"
            
            return False, f"Download failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe storage"""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        return filename