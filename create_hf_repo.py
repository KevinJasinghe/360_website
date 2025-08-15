#!/usr/bin/env python3
"""
Create a Hugging Face repository and upload the model
This will create a public repository to host the piano transcription model
"""

import os
import shutil
from pathlib import Path

def create_manual_upload_instructions():
    """Create instructions for manual upload to Hugging Face"""
    
    print("🚀 Manual Upload Instructions for Hugging Face Hub")
    print("=" * 60)
    
    # Check if model exists
    model_path = "final_model"
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return
    
    model_size = os.path.getsize(model_path) / (1024 * 1024)
    print(f"📊 Model size: {model_size:.1f} MB")
    
    print("\n📋 Steps to upload manually:")
    print("1. Go to https://huggingface.co/new")
    print("2. Create a new model repository:")
    print("   - Repository name: piano-transcription-model")
    print("   - Owner: your-username")
    print("   - License: MIT")
    print("   - Make it public")
    
    print("\n3. Clone the repository:")
    print("   git clone https://huggingface.co/your-username/piano-transcription-model")
    
    print("\n4. Copy the model file:")
    print(f"   cp {model_path} piano-transcription-model/pytorch_model.bin")
    
    print("\n5. Create README.md with model info")
    print("6. Git add, commit, and push:")
    print("   cd piano-transcription-model")
    print("   git add .")
    print("   git commit -m 'Add piano transcription model'")
    print("   git push")
    
    # Create a temporary directory with all needed files
    temp_dir = "hf_upload_temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Copy model file
    shutil.copy2(model_path, os.path.join(temp_dir, "pytorch_model.bin"))
    
    # Create README
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
- **Training**: Trained for piano music transcription

## Usage

```python
import torch
import requests

# Download the model
url = "https://huggingface.co/your-username/piano-transcription-model/resolve/main/pytorch_model.bin"
response = requests.get(url)
with open("model.bin", "wb") as f:
    f.write(response.content)

# Load the model
model = torch.load("model.bin", map_location='cpu')
```

## Applications

- Convert piano recordings to MIDI files
- Music transcription and analysis
- Educational tools for music learning

## License

MIT License - Feel free to use for research and commercial applications.
"""
    
    with open(os.path.join(temp_dir, "README.md"), "w") as f:
        f.write(readme_content)
    
    print(f"\n📁 Files prepared in '{temp_dir}' directory:")
    print("   - pytorch_model.bin (the model file)")
    print("   - README.md (model documentation)")
    
    print(f"\n💡 Alternative: Use a temporary file hosting service:")
    print("   - Upload to file.io, transfer.sh, or similar")
    print("   - Get the direct download URL")
    print("   - Update MODEL_URL in model_downloader.py")

if __name__ == "__main__":
    create_manual_upload_instructions()