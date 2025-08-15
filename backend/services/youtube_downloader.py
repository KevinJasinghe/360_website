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
        # Try multiple strategies for getting video info - Enhanced Aug 2025
        strategies = [
            {
                'name': 'mweb_tier_2',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['mweb'],
                        'player_skip': ['webpage', 'configs'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin'
                }
            },
            {
                'name': 'ios_creator',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios_creator'],
                        'player_skip': ['webpage'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.ios.ytcreator/1.19.8.15622 (iPhone15,2; U; CPU iOS 16_6 like Mac OS X)',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
            {
                'name': 'android_vr',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android_vr'],
                        'player_skip': ['webpage'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.android.apps.youtube.vr.oculus/1.56.21 (Linux; U; Android 12; eureka-user Build/SQ3A.220605.009.A1)',
                    'Accept': '*/*'
                }
            },
            {
                'name': 'ios_music',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios_music'],
                        'player_skip': ['webpage'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.ios.youtubemusic/6.42.52 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)',
                    'Accept': '*/*'
                }
            },
            {
                'name': 'tv_embedded_fallback',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['tv_embedded'],
                        'player_skip': ['webpage', 'configs'],
                        'include_incomplete_formats': False
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (ChromiumStylePlatform) Cobalt/40.13031-qa (unlike Gecko) v8/8.5.210.20 gles Starboard/15',
                    'Accept': '*/*'
                }
            }
        ]
        
        last_error = None
        for strategy in strategies:
            try:
                print(f"🔄 Trying info strategy: {strategy['name']}")
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': strategy['extractor_args'],
                    'http_headers': strategy['http_headers'],
                    'socket_timeout': 10,
                    'retries': 0,  # No retries per strategy to fail fast
                    'fragment_retries': 0,
                    'skip_unavailable_fragments': True,
                    'geo_bypass': True,
                    'no_check_certificate': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    print(f"✅ Info strategy {strategy['name']} succeeded")
                    break  # Success, exit loop
                    
            except Exception as e:
                print(f"❌ Info strategy {strategy['name']} failed: {str(e)[:100]}")
                last_error = e
                if strategy == strategies[-1]:  # Last strategy
                    raise last_error  # Re-raise the last error
                continue
        
        try:
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
            
            # Try multiple download strategies to avoid bot detection - Enhanced Aug 2025
            strategies = [
                {
                    'name': 'mweb_tier_2',
                    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best[filesize<100M]',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['mweb'],
                            'player_skip': ['webpage', 'configs'],
                        }
                    },
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin'
                    }
                },
                {
                    'name': 'ios_creator',
                    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best[filesize<100M]',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios_creator'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'http_headers': {
                        'User-Agent': 'com.google.ios.ytcreator/1.19.8.15622 (iPhone15,2; U; CPU iOS 16_6 like Mac OS X)',
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9'
                    }
                },
                {
                    'name': 'android_vr',
                    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best[filesize<100M]',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android_vr'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'http_headers': {
                        'User-Agent': 'com.google.android.apps.youtube.vr.oculus/1.56.21 (Linux; U; Android 12; eureka-user Build/SQ3A.220605.009.A1)',
                        'Accept': '*/*'
                    }
                },
                {
                    'name': 'ios_music',
                    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best[filesize<100M]',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios_music'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'http_headers': {
                        'User-Agent': 'com.google.ios.youtubemusic/6.42.52 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)',
                        'Accept': '*/*'
                    }
                },
                {
                    'name': 'tv_embedded_final',
                    'format': 'bestaudio[ext=m4a]/bestaudio/best[filesize<100M]',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['tv_embedded'],
                            'player_skip': ['webpage', 'configs'],
                            'include_incomplete_formats': False
                        }
                    },
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (ChromiumStylePlatform) Cobalt/40.13031-qa (unlike Gecko) v8/8.5.210.20 gles Starboard/15',
                        'Accept': '*/*'
                    }
                }
            ]
            
            for strategy in strategies:
                try:
                    print(f"🔄 Trying download strategy: {strategy['name']}")
                    
                    ydl_opts = {
                        'format': strategy['format'],
                        'outtmpl': output_path.replace('.wav', '.%(ext)s'),
                        'noplaylist': True,
                        'quiet': True,  # Reduce noise for multiple attempts
                        'no_warnings': True,
                        'extract_flat': False,
                        'socket_timeout': 15,
                        'retries': 0,  # No retries per strategy to fail fast
                        'fragment_retries': 0,
                        'skip_unavailable_fragments': True,
                        'geo_bypass': True,
                        'no_check_certificate': True,
                        'extractor_args': strategy['extractor_args'],
                        'http_headers': strategy['http_headers']
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    # If we get here, download was successful
                    print(f"✅ Download successful with strategy: {strategy['name']}")
                    break
                    
                except Exception as e:
                    print(f"❌ Strategy {strategy['name']} failed: {str(e)}")
                    if strategy == strategies[-1]:  # Last strategy
                        raise e  # Re-raise the last error
                    continue
            
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