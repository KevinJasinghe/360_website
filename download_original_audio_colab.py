# =============================================================================
# DOWNLOAD ORIGINAL AUDIO FROM OVERFITTED TRAINING DATA
# =============================================================================

# ❌ WARNING: Your overfitted model is NOT training on the original MAESTRO audio!
# 
# Here's what happens to the audio in your training pipeline:
# 
# 1. Original MAESTRO audio (.wav) → loaded with librosa
# 2. Resampled to 16kHz mono
# 3. Volume normalized 
# 4. Converted to mel spectrogram (LOSES phase information)
# 5. Split into 10-second windows
# 6. 50% chance: Mixed with MUSDB drums/bass/vocals 
# 
# Your model trains on PROCESSED + MIXED audio, not the original!

# SOLUTION: Get the processed audio that matches your training
# ============================================================

import torch
import numpy as np
import soundfile as sf
from google.colab import files
import shutil

# Get sample 0 from your overfitted training subset
overfit_loader = create_memory_efficient_overfit_loader(train_dataset, num_examples=5, batch_size=1)

# Get the EXACT audio data your model was trained on
sample_batch = next(iter(overfit_loader))
audio_features = sample_batch['audio'][0]  # First sample, shape: (312, 128)
metadata = sample_batch['metadata'][0]

print(f"Training sample info:")
print(f"Title: {metadata['title']}")
print(f"Composer: {metadata['composer']}")
print(f"Audio features shape: {audio_features.shape}")
print(f"Duration: ~{audio_features.shape[0] * 512 / 16000:.1f} seconds")

# The audio_features are mel spectrograms - we CANNOT convert back to original audio
# But we can download the original MAESTRO file and show you the difference

# DOWNLOAD THE ORIGINAL MAESTRO FILE
# ===================================
original_audio_path = metadata['audio_path']
original_midi_path = metadata['midi_path']

# Fix the path (your cache has wrong directory name)
correct_audio_path = str(original_audio_path).replace('APS360_Piano_Transcription', 'APS360_Team_2_Project')
correct_midi_path = str(original_midi_path).replace('APS360_Piano_Transcription', 'APS360_Team_2_Project')

print(f"\nOriginal file paths:")
print(f"Audio: {correct_audio_path}")
print(f"MIDI: {correct_midi_path}")

# Check if files exist and download
import os
if os.path.exists(correct_audio_path) and os.path.exists(correct_midi_path):
    print("✅ Files found! Downloading...")
    
    # Get just the filename part for the 2009 file
    filename_part = "MIDI-Unprocessed_18_R1_2009_01-03_ORIG_MID--AUDIO_18_R1_2009_18_R1_2009_02_WAV"
    
    # Copy files for download
    shutil.copy(correct_audio_path, f'original_maestro_audio_{filename_part}.wav')
    shutil.copy(correct_midi_path, f'original_maestro_midi_{filename_part}.mid')
    
    # Download files
    files.download(f'original_maestro_audio_{filename_part}.wav')
    files.download(f'original_maestro_midi_{filename_part}.mid')
    
    print("✅ Downloaded original MAESTRO files!")
    print(f"📊 This is an 11+ minute recording")
    print(f"📊 Your model only sees 10-second windows from this")
    print(f"📊 Plus 50% chance of MUSDB mixing")
    
else:
    print("❌ Files not found. Check the paths manually in Google Drive.")
    print("Navigate to: APS360_Team_2_Project → data → raw → maestro-v3.0.0 → 2009")
    print(f"Look for files containing: {filename_part}")

# IMPORTANT DIFFERENCES:
# ======================
print(f"\n🔍 KEY DIFFERENCES:")
print(f"📁 Original MAESTRO: 11+ minute full piano performance")
print(f"🔪 Training data: 10-second windows only") 
print(f"🎵 Training audio: 50% chance mixed with drums/bass/vocals")
print(f"📊 Training features: Mel spectrograms (no phase info)")
print(f"🎯 Your overfitted model: Memorized these specific 10-second processed chunks")

# =============================================================================