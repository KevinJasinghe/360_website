import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs
import subprocess
import json
import tempfile

# Import pytubefix as primary alternative
try:
    from pytubefix import YouTube as PytubeFixYouTube
    from pytubefix.exceptions import VideoUnavailable, PytubeFixError
    PYTUBEFIX_AVAILABLE = True
    print("✅ PytubeFixed loaded successfully")
except ImportError:
    PYTUBEFIX_AVAILABLE = False
    print("⚠️ PytubeFixed not available - will use yt-dlp only")

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
    def get_video_info_pytubefix(url):
        """Get video info using pytubefix - more reliable than yt-dlp for 2025"""
        if not PYTUBEFIX_AVAILABLE:
            return None, "PytubeFixed not available"
        
        try:
            print("🔄 Trying pytubefix info extraction")
            yt = PytubeFixYouTube(url, use_oauth=False, allow_oauth_cache=False)
            
            # Get basic info
            info = {
                'title': yt.title or 'Unknown',
                'duration': yt.length or 0,
                'video_id': yt.video_id or '',
                'uploader': yt.author or 'Unknown'
            }
            
            print("✅ PytubeFixed info extraction succeeded")
            return info, None
            
        except VideoUnavailable as e:
            return None, f"Video unavailable: {str(e)}"
        except PytubeFixError as e:
            return None, f"PytubeFixed error: {str(e)}"
        except Exception as e:
            return None, f"PytubeFixed unexpected error: {str(e)}"

    @staticmethod
    def download_audio_pytubefix(url, output_path, max_duration=600):
        """Download audio using pytubefix - more reliable than yt-dlp for 2025"""
        if not PYTUBEFIX_AVAILABLE:
            return False, "PytubeFixed not available"
        
        try:
            print("🔄 Trying pytubefix audio download")
            yt = PytubeFixYouTube(url, use_oauth=False, allow_oauth_cache=False)
            
            # Get the best audio stream
            audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
            if not audio_stream:
                # Fallback to any audio stream
                audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                return False, "No audio streams available"
            
            # Download to the specified path
            base_path = output_path.replace('.wav', '')
            output_file = f"{base_path}.m4a"
            
            # Download the file
            audio_stream.download(output_path=os.path.dirname(output_path), 
                                filename=os.path.basename(output_file))
            
            if os.path.exists(output_file):
                print("✅ PytubeFixed audio download succeeded")
                return True, f"PytubeFixed download successful: {output_file}"
            else:
                return False, "PytubeFixed download completed but file not found"
                
        except VideoUnavailable as e:
            return False, f"Video unavailable: {str(e)}"
        except PytubeFixError as e:
            return False, f"PytubeFixed download error: {str(e)}"
        except Exception as e:
            return False, f"PytubeFixed unexpected error: {str(e)}"

    @staticmethod
    def get_video_info_cli(url):
        """Get video info using yt-dlp command line - sometimes more reliable"""
        try:
            cmd = [
                'yt-dlp',
                '--print', '%(title)s|%(duration)s|%(id)s|%(uploader)s',
                '--no-warnings',
                '--quiet',
                '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                '--add-header', 'Accept:*/*',
                '--add-header', 'Accept-Language:en-US,en;q=0.9',
                '--referer', 'https://www.youtube.com/',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout:
                parts = result.stdout.strip().split('|')
                if len(parts) >= 4:
                    return {
                        'title': parts[0],
                        'duration': int(parts[1]) if parts[1].isdigit() else 0,
                        'video_id': parts[2],
                        'uploader': parts[3]
                    }, None
            
            return None, f"CLI extraction failed: {result.stderr}"
            
        except Exception as e:
            return None, f"CLI method error: {str(e)}"

    @staticmethod
    def get_video_info(url):
        """Get video information without downloading"""
        # Try multiple strategies for getting video info - Production-optimized Aug 2025
        strategies = [
            {
                'name': 'server_android_vr',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android_vr'],
                        'player_skip': ['webpage', 'configs'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.android.apps.youtube.vr.oculus/1.56.21 (Linux; U; Android 12; eureka-user Build/SQ3A.220605.009.A1)',
                    'Accept': '*/*',
                    'X-Forwarded-For': '8.8.8.8',  # Google DNS to appear less server-like
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            },
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
        
        # Try pytubefix first (primary method for 2025)
        if PYTUBEFIX_AVAILABLE:
            pytubefix_info, pytubefix_error = YouTubeDownloader.get_video_info_pytubefix(url)
            if pytubefix_info:
                info = pytubefix_info
            else:
                print(f"❌ PytubeFixed failed: {pytubefix_error}")
        
        # If pytubefix failed, try yt-dlp strategies
        if 'info' not in locals():
            last_error = None
            for strategy in strategies:
                try:
                    print(f"🔄 Trying yt-dlp strategy: {strategy['name']}")
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
                        print(f"✅ yt-dlp strategy {strategy['name']} succeeded")
                        break  # Success, exit loop
                        
                except Exception as e:
                    print(f"❌ yt-dlp strategy {strategy['name']} failed: {str(e)[:100]}")
                    last_error = e
                    if strategy == strategies[-1]:  # Last strategy failed, try CLI fallback
                        print("🔄 All yt-dlp strategies failed, trying CLI fallback")
                        cli_info, cli_error = YouTubeDownloader.get_video_info_cli(url)
                        if cli_info:
                            info = cli_info
                            print("✅ CLI fallback succeeded")
                            break
                        else:
                            print(f"❌ CLI fallback failed: {cli_error}")
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
    def download_audio_cli(url, output_path, max_duration=600):
        """Download audio using yt-dlp CLI - sometimes more reliable than Python API"""
        try:
            # Use yt-dlp command line with aggressive bot bypass
            cmd = [
                'yt-dlp',
                '--format', 'bestaudio[ext=m4a]/bestaudio/best',
                '--output', output_path.replace('.wav', '.%(ext)s'),
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                '--user-agent', 'com.google.ios.youtubemusic/6.42.52 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)',
                '--add-header', 'Accept:*/*',
                '--add-header', 'Accept-Language:en-US,en;q=0.9',
                '--referer', 'https://www.youtube.com/',
                '--socket-timeout', '15',
                '--retries', '0',
                '--fragment-retries', '0',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Check if file was created
                base_path = output_path.replace('.wav', '')
                possible_files = [
                    f"{base_path}.m4a", 
                    f"{base_path}.webm",
                    f"{base_path}.mp4",
                    f"{base_path}.opus",
                    output_path
                ]
                
                for possible_file in possible_files:
                    if os.path.exists(possible_file):
                        return True, f"CLI download successful: {possible_file}"
                
                return False, "CLI download completed but file not found"
            else:
                return False, f"CLI download failed: {result.stderr}"
                
        except Exception as e:
            return False, f"CLI download error: {str(e)}"

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
            
            # Try multiple download strategies to avoid bot detection - Production-optimized Aug 2025
            strategies = [
                {
                    'name': 'server_android_vr',
                    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best[filesize<100M]',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android_vr'],
                            'player_skip': ['webpage', 'configs'],
                        }
                    },
                    'http_headers': {
                        'User-Agent': 'com.google.android.apps.youtube.vr.oculus/1.56.21 (Linux; U; Android 12; eureka-user Build/SQ3A.220605.009.A1)',
                        'Accept': '*/*',
                        'X-Forwarded-For': '8.8.8.8',  # Google DNS to appear less server-like
                        'Accept-Language': 'en-US,en;q=0.9'
                    }
                },
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
            
            # Try pytubefix first (primary method for 2025)
            download_success = False
            success_message = ""
            if PYTUBEFIX_AVAILABLE:
                pytubefix_success, pytubefix_message = YouTubeDownloader.download_audio_pytubefix(url, output_path, max_duration)
                if pytubefix_success:
                    download_success = True
                    success_message = pytubefix_message
                    print("✅ PytubeFixed download completed, skipping yt-dlp strategies")
                else:
                    print(f"❌ PytubeFixed download failed: {pytubefix_message}")
            
            # If pytubefix failed, try yt-dlp strategies
            if not download_success:
                for strategy in strategies:
                    try:
                        print(f"🔄 Trying yt-dlp strategy: {strategy['name']}")
                        
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
                        print(f"✅ yt-dlp download successful with strategy: {strategy['name']}")
                        download_success = True
                        break
                        
                    except Exception as e:
                        print(f"❌ yt-dlp strategy {strategy['name']} failed: {str(e)}")
                        if strategy == strategies[-1]:  # Last strategy failed, try CLI fallback
                            print("🔄 All yt-dlp strategies failed, trying CLI fallback")
                            cli_success, cli_message = YouTubeDownloader.download_audio_cli(url, output_path, max_duration)
                            if cli_success:
                                print("✅ CLI fallback download succeeded")
                                return cli_success, cli_message
                            else:
                                print(f"❌ CLI fallback failed: {cli_message}")
                                raise e  # Re-raise the last error
                        continue
            
            # If pytubefix succeeded, return its result
            if download_success and success_message:
                return True, success_message
            
            # Otherwise check if yt-dlp file was actually downloaded
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