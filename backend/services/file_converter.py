import ffmpeg
import os
import subprocess

class FileConverter:
    SUPPORTED_FORMATS = [
        '.mp3', '.mp4', '.wav', '.avi', '.mov', 
        '.m4a', '.flac', '.ogg', '.webm', '.mkv'
    ]
    
    @staticmethod
    def is_supported_format(filename):
        """Check if the file format is supported"""
        _, ext = os.path.splitext(filename.lower())
        return ext in FileConverter.SUPPORTED_FORMATS
    
    @staticmethod
    def convert_to_wav(input_path, output_path):
        """Convert audio/video file to WAV format using ffmpeg"""
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            
            # Convert to WAV using ffmpeg-python
            (
                ffmpeg
                .input(input_path)
                .output(output_path, format='wav', acodec='pcm_s16le', ar=44100, ac=1)
                .overwrite_output()
                .run(quiet=True)
            )
            
            return True, "Conversion successful"
            
        except subprocess.CalledProcessError:
            return False, "FFmpeg not found. Please install FFmpeg."
        except ffmpeg.Error as e:
            return False, f"Conversion failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def get_audio_info(file_path):
        """Get audio information using ffprobe"""
        try:
            probe = ffmpeg.probe(file_path)
            audio_stream = next((stream for stream in probe['streams'] 
                               if stream['codec_type'] == 'audio'), None)
            
            if not audio_stream:
                return None, "No audio stream found"
            
            duration = float(probe['format']['duration'])
            sample_rate = int(audio_stream.get('sample_rate', 0))
            channels = int(audio_stream.get('channels', 0))
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels,
                'format': probe['format']['format_name']
            }, None
            
        except Exception as e:
            return None, f"Error getting audio info: {str(e)}"