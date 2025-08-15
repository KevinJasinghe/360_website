"""
Model downloader for Railway deployment
Downloads the trained model file on first startup if not present
"""
import os
import requests
from pathlib import Path
import hashlib

class ModelDownloader:
    
    # You'll need to upload your model to a public URL (GitHub releases, Google Drive, etc.)
    MODEL_URL = "https://github.com/KevinJasinghe/360_website/releases/download/v1.0/model_training_model_epochs21_lr0.001_weight_decay0.0001_start20250814_165547_endongoing_epoch021.pth"
    MODEL_FILENAME = "final_model"
    EXPECTED_SIZE = 89903178  # Size in bytes of your model
    
    @classmethod
    def get_model_path(cls):
        """Get the expected path for the model file"""
        return cls.MODEL_FILENAME
    
    @classmethod
    def is_model_available(cls):
        """Check if model file exists and is valid"""
        model_path = cls.get_model_path()
        if not os.path.exists(model_path):
            return False
        
        # Check file size
        actual_size = os.path.getsize(model_path)
        if actual_size != cls.EXPECTED_SIZE:
            print(f"⚠️  Model file size mismatch: expected {cls.EXPECTED_SIZE}, got {actual_size}")
            return False
        
        return True
    
    @classmethod
    def download_model(cls):
        """Download the model file if it doesn't exist"""
        model_path = cls.get_model_path()
        
        if cls.is_model_available():
            print(f"✅ Model already exists: {model_path}")
            return True
        
        print(f"📥 Downloading model file...")
        print(f"   URL: {cls.MODEL_URL}")
        print(f"   Destination: {model_path}")
        
        try:
            # Create a temporary download
            temp_path = f"{model_path}.tmp"
            
            response = requests.get(cls.MODEL_URL, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"   Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")
            
            # Verify download
            actual_size = os.path.getsize(temp_path)
            if actual_size == cls.EXPECTED_SIZE:
                # Move to final location
                os.rename(temp_path, model_path)
                print(f"✅ Model downloaded successfully: {model_path} ({actual_size} bytes)")
                return True
            else:
                print(f"❌ Download size mismatch: expected {cls.EXPECTED_SIZE}, got {actual_size}")
                os.remove(temp_path)
                return False
                
        except Exception as e:
            print(f"❌ Model download failed: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    @classmethod
    def ensure_model_available(cls):
        """Ensure model is available, download if necessary"""
        if cls.is_model_available():
            return True
        
        print("🤖 Model not found locally, attempting download...")
        return cls.download_model()


# Alternative: Use environment variable for model URL
class EnvironmentModelDownloader(ModelDownloader):
    """Version that uses environment variables for flexibility"""
    
    @classmethod
    def get_model_url(cls):
        return os.environ.get('MODEL_DOWNLOAD_URL', cls.MODEL_URL)
    
    @classmethod  
    def download_model(cls):
        """Download using environment variable URL"""
        cls.MODEL_URL = cls.get_model_url()
        return super().download_model()