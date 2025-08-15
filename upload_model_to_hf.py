#!/usr/bin/env python3
"""
Upload the piano transcription model to Hugging Face Hub
Run this script to upload the model: python upload_model_to_hf.py
"""

import os
from pathlib import Path
from huggingface_hub import HfApi, login

def upload_model():
    """Upload the piano transcription model to Hugging Face Hub"""
    
    # Check if model file exists
    model_path = "final_model"
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return False
    
    # Get model info
    model_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
    print(f"📊 Model size: {model_size:.1f} MB")
    
    try:
        # Login to Hugging Face (will prompt for token)
        print("🔐 Please login to Hugging Face...")
        login()
        
        # Initialize API
        api = HfApi()
        
        # Repository details
        repo_id = "kevinjasinghe/piano-transcription-model"
        
        print(f"📤 Uploading model to {repo_id}...")
        
        # Create repository if it doesn't exist
        try:
            api.create_repo(repo_id=repo_id, exist_ok=True, repo_type="model")
            print(f"✅ Repository created/verified: {repo_id}")
        except Exception as e:
            print(f"⚠️  Repository creation warning: {e}")
        
        # Upload the model file
        api.upload_file(
            path_or_fileobj=model_path,
            path_in_repo="pytorch_model.bin",
            repo_id=repo_id,
            commit_message="Upload piano transcription model"
        )
        
        # Create a README for the model
        readme_content = """---
license: mit
language:
- en
tags:
- audio
- music
- piano
- transcription
- pytorch
library_name: pytorch
---

# Piano Transcription Model

This is a PyTorch model trained for piano transcription - converting audio recordings of piano music into MIDI format.

## Model Architecture

- **Model Type**: CRNN (Convolutional Recurrent Neural Network)
- **Input**: Mel spectrogram features (128 mel bins)
- **Output**: Piano note onsets and frames
- **Training**: 21 epochs with learning rate 0.001

## Usage

```python
import torch
from huggingface_hub import hf_hub_download

# Download the model
model_path = hf_hub_download(
    repo_id="kevinjasinghe/piano-transcription-model",
    filename="pytorch_model.bin"
)

# Load the model
model = torch.load(model_path, map_location='cpu')
```

## Training Details

- **Dataset**: Piano audio recordings
- **Preprocessing**: Audio converted to mel spectrograms
- **Architecture**: CNN layers followed by bidirectional LSTM
- **Output**: Note onset detection and frame-level predictions

## Applications

- Convert piano recordings to MIDI files
- Music transcription and analysis
- Educational tools for music learning

## License

MIT License - Feel free to use for research and commercial applications.
"""
        
        # Upload README
        api.upload_file(
            path_or_fileobj=readme_content.encode(),
            path_in_repo="README.md",
            repo_id=repo_id,
            commit_message="Add model documentation"
        )
        
        print(f"✅ Model uploaded successfully!")
        print(f"🔗 Model URL: https://huggingface.co/{repo_id}")
        print(f"📥 Download URL: https://huggingface.co/{repo_id}/resolve/main/pytorch_model.bin")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Piano Transcription Model Upload to Hugging Face Hub")
    print("=" * 60)
    
    success = upload_model()
    
    if success:
        print("\n✅ Upload completed successfully!")
        print("🔄 Update your model downloader to use the new URL")
    else:
        print("\n❌ Upload failed. Please check the error messages above.")