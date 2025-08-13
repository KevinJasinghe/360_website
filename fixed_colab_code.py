# =============================================================================
# FIXED GOOGLE COLAB CODE - Copy and paste this
# =============================================================================

# The issue: Your cached dataset has wrong paths. Let's find and download files manually.

# STEP 1: Find the actual MAESTRO files in your drive
# ==================================================
import os
import shutil
from google.colab import files

def find_maestro_files_in_drive():
    """Search for MAESTRO files in all APS360 folders"""
    base_path = "/content/drive/MyDrive"
    maestro_files = {'audio': [], 'midi': []}
    
    # Check both APS360 folders
    aps360_folders = [
        "APS360_Team_2_Project",
        "APS360_Team_2_Project (1)"
    ]
    
    for folder in aps360_folders:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path):
            print(f"Checking {folder}...")
            
            # Walk through the directory tree
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if 'maestro' in root.lower():
                        full_path = os.path.join(root, file)
                        if file.endswith('.wav'):
                            maestro_files['audio'].append(full_path)
                        elif file.endswith('.mid') or file.endswith('.midi'):
                            maestro_files['midi'].append(full_path)
                        
                        # Stop after finding a few files
                        if len(maestro_files['audio']) >= 3:
                            break
                if len(maestro_files['audio']) >= 3:
                    break
    
    return maestro_files

# Find MAESTRO files
print("🔍 Searching for MAESTRO files in your drive...")
maestro_files = find_maestro_files_in_drive()

print(f"📊 Found {len(maestro_files['audio'])} audio files")
print(f"📊 Found {len(maestro_files['midi'])} MIDI files")

# Show first few files found
if maestro_files['audio']:
    print("\n🎵 Audio files found:")
    for i, audio_file in enumerate(maestro_files['audio'][:3]):
        print(f"  {i}: {audio_file}")

if maestro_files['midi']:
    print("\n🎼 MIDI files found:")
    for i, midi_file in enumerate(maestro_files['midi'][:3]):
        print(f"  {i}: {midi_file}")

# =============================================================================

# STEP 2: Download the first pair of files found
# ===============================================
if maestro_files['audio'] and maestro_files['midi']:
    # Get first audio and MIDI file
    first_audio = maestro_files['audio'][0]
    first_midi = maestro_files['midi'][0]
    
    print(f"\n📥 Downloading files:")
    print(f"Audio: {os.path.basename(first_audio)}")
    print(f"MIDI: {os.path.basename(first_midi)}")
    
    try:
        # Copy files for download
        shutil.copy(first_audio, 'maestro_original_audio.wav')
        shutil.copy(first_midi, 'maestro_original_midi.mid')
        
        # Download files
        files.download('maestro_original_audio.wav')
        files.download('maestro_original_midi.mid')
        
        print("✅ Successfully downloaded MAESTRO files!")
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        
else:
    print("❌ No MAESTRO files found. The dataset might not be downloaded yet.")

# =============================================================================

# ALTERNATIVE: Download from specific known locations
# ===================================================
# If the search doesn't work, try these common paths:

known_paths = [
    "/content/drive/MyDrive/APS360_Team_2_Project/data/raw/maestro-v3.0.0",
    "/content/drive/MyDrive/APS360_Team_2_Project (1)/data/raw/maestro-v3.0.0",
]

print("\n🔍 Checking known MAESTRO locations...")
for path in known_paths:
    if os.path.exists(path):
        print(f"✅ Found: {path}")
        
        # List contents
        try:
            contents = os.listdir(path)
            print(f"  Contains: {len(contents)} items")
            
            # Find first year folder
            for item in contents:
                if item.isdigit() and len(item) == 4:  # Year folder like "2009"
                    year_path = os.path.join(path, item)
                    print(f"  Found year: {item}")
                    
                    # List files in year folder
                    year_files = os.listdir(year_path)
                    audio_files = [f for f in year_files if f.endswith('.wav')]
                    midi_files = [f for f in year_files if f.endswith('.mid') or f.endswith('.midi')]
                    
                    if audio_files and midi_files:
                        # Download first pair
                        audio_path = os.path.join(year_path, audio_files[0])
                        midi_path = os.path.join(year_path, midi_files[0])
                        
                        print(f"📥 Downloading: {audio_files[0]}")
                        shutil.copy(audio_path, 'maestro_sample_original.wav')
                        shutil.copy(midi_path, 'maestro_sample_original.mid')
                        
                        files.download('maestro_sample_original.wav')
                        files.download('maestro_sample_original.mid')
                        
                        print("✅ Downloaded original MAESTRO files!")
                        break
                    break
        except Exception as e:
            print(f"  Error reading: {e}")
    else:
        print(f"❌ Not found: {path}")

# =============================================================================