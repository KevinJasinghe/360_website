# =============================================================================
# GOOGLE COLAB CODE - Copy and paste these code blocks
# =============================================================================

# BLOCK 1: Check file paths and drive structure
# ============================================
import os

sample_0_data = train_dataset[0]
metadata = sample_0_data['metadata']

original_audio_path = metadata['audio_path']
original_midi_path = metadata['midi_path']

print(f"Expected audio path: {original_audio_path}")
print(f"Audio file exists: {os.path.exists(original_audio_path)}")

print(f"Expected MIDI path: {original_midi_path}")
print(f"MIDI file exists: {os.path.exists(original_midi_path)}")

# Check actual drive structure
base_path = "/content/drive/MyDrive"
print(f"\nContents of {base_path}:")
for item in os.listdir(base_path):
    if os.path.isdir(os.path.join(base_path, item)):
        print(f"📁 {item}")
    else:
        print(f"📄 {item}")

# Look for APS360 or maestro folders
print(f"\nLooking for APS360/maestro folders:")
for item in os.listdir(base_path):
    if "APS360" in item or "maestro" in item.lower():
        full_path = os.path.join(base_path, item)
        print(f"Found: {full_path}")
        if os.path.isdir(full_path):
            try:
                subcontents = os.listdir(full_path)[:10]  # First 10 items
                print(f"  Contains: {subcontents}")
            except:
                print(f"  Cannot read contents")

# =============================================================================

# BLOCK 2: Download original files (use after finding correct paths)
# =================================================================
# First update the paths based on what you found above
# Then run this block

import shutil
from google.colab import files

# UPDATE THESE PATHS based on what you found in BLOCK 1
# Replace with actual paths found in your drive
actual_audio_path = original_audio_path  # Update this
actual_midi_path = original_midi_path    # Update this

# Check files exist
if os.path.exists(actual_audio_path) and os.path.exists(actual_midi_path):
    print(f"✅ Files found!")
    print(f"Audio: {actual_audio_path}")
    print(f"MIDI: {actual_midi_path}")
    
    # Copy files for download
    shutil.copy(actual_audio_path, 'maestro_sample_0_original.wav')
    shutil.copy(actual_midi_path, 'maestro_sample_0_original.mid')
    
    # Download files
    files.download('maestro_sample_0_original.wav')
    files.download('maestro_sample_0_original.mid')
    
    print("✅ Downloaded original MAESTRO files!")
    
else:
    print("❌ Files not found. Update the paths in this block.")
    print(f"Audio exists: {os.path.exists(actual_audio_path)}")
    print(f"MIDI exists: {os.path.exists(actual_midi_path)}")

# =============================================================================

# BLOCK 3: Alternative - Find and download any MAESTRO sample
# ==========================================================
# If paths are too complex, just find any MAESTRO file

def find_maestro_files():
    """Find any MAESTRO files in the drive"""
    maestro_files = []
    base_path = "/content/drive/MyDrive"
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.wav') and 'maestro' in root.lower():
                full_path = os.path.join(root, file)
                maestro_files.append(full_path)
                if len(maestro_files) >= 5:  # Find first 5
                    break
        if len(maestro_files) >= 5:
            break
    
    return maestro_files

# Find MAESTRO files
maestro_files = find_maestro_files()
print(f"Found {len(maestro_files)} MAESTRO files:")
for i, file_path in enumerate(maestro_files):
    print(f"{i}: {file_path}")

# Download first file if found
if maestro_files:
    first_file = maestro_files[0]
    filename = os.path.basename(first_file)
    
    print(f"Downloading: {filename}")
    shutil.copy(first_file, f'maestro_sample_{filename}')
    files.download(f'maestro_sample_{filename}')
    print("✅ Downloaded!")
else:
    print("❌ No MAESTRO files found")

# =============================================================================