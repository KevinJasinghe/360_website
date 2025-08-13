"""
Audio Processing Pipeline - Extracted from training.ipynb
Handles audio loading, preprocessing, and feature extraction for piano transcription
"""

import numpy as np
import librosa
import torch
from pathlib import Path


# Configuration constants (from training.ipynb)
SAMPLE_RATE = 16000
N_MELS = 128
N_FFT = 2048
HOP_LENGTH = 512
WINDOW_SIZE_SECONDS = 10.0
MIN_RECORDING_LENGTH = 5.0


def standardize_audio(audio_path: Path) -> tuple[np.ndarray, int]:
    """
    Standardize audio: resample to 16kHz mono and normalize volume
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        tuple: (audio array, sample rate) or (None, None) if error
    """
    try:
        # Convert Path to string if necessary
        audio_path_str = str(audio_path)
        
        # Load and convert to mono
        audio, sr = librosa.load(audio_path_str, sr=None, mono=True)

        # Resample if needed
        if sr != SAMPLE_RATE:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)

        # Normalize volume
        rms = np.sqrt(np.mean(audio**2))
        if rms > 1e-6:
            audio = audio * (0.1 / rms)  # Normalize to target RMS
            audio = np.clip(audio, -0.95, 0.95)  # Prevent clipping

        return audio, SAMPLE_RATE
    except Exception as e:
        print(f"Audio error {audio_path}: {e}")
        return None, None


def extract_audio_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    Extract mel spectrogram features
    
    Args:
        audio: Audio array
        sr: Sample rate
        
    Returns:
        features: Mel spectrogram features (time, mel_bins) or None if error
    """
    try:
        mel_spec = librosa.feature.melspectrogram(
            y=audio, sr=sr, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_spec_norm = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-8)
        features = mel_spec_norm.T  # (time, features)
        
        return features
    except Exception as e:
        print(f"Feature extraction error: {e}")
        return None


def process_audio_for_inference(audio_path: str, max_length_seconds: float = None) -> torch.Tensor:
    """
    Complete audio processing pipeline for model inference
    
    Args:
        audio_path: Path to audio file
        max_length_seconds: Maximum length to process (None for full length)
        
    Returns:
        torch.Tensor: Processed audio features [1, 128, T] ready for model input
        None if processing failed
    """
    try:
        # Step 1: Load and standardize audio
        audio, sr = standardize_audio(audio_path)
        if audio is None:
            return None
            
        # Step 2: Truncate if needed
        if max_length_seconds is not None:
            max_samples = int(max_length_seconds * sr)
            if len(audio) > max_samples:
                audio = audio[:max_samples]
        
        # Step 3: Check minimum length
        min_samples = int(MIN_RECORDING_LENGTH * sr)
        if len(audio) < min_samples:
            print(f"Audio too short: {len(audio)/sr:.1f}s (minimum {MIN_RECORDING_LENGTH}s)")
            return None
            
        # Step 4: Extract features
        features = extract_audio_features(audio, sr)
        if features is None:
            return None
            
        # Step 5: Convert to tensor and add batch dimension
        # features shape: (time, 128) -> (1, 128, time)
        features_tensor = torch.FloatTensor(features.T).unsqueeze(0)
        
        print(f"✅ Processed audio: {len(audio)/sr:.1f}s -> {features_tensor.shape}")
        return features_tensor
        
    except Exception as e:
        print(f"❌ Audio processing failed: {e}")
        return None


def chunk_audio_features(features: torch.Tensor, chunk_size_seconds: float = WINDOW_SIZE_SECONDS) -> list[torch.Tensor]:
    """
    Split long audio features into smaller chunks for processing
    
    Args:
        features: Audio features tensor [1, 128, T]
        chunk_size_seconds: Size of each chunk in seconds
        
    Returns:
        List of feature chunks [1, 128, chunk_frames]
    """
    if features.dim() != 3 or features.shape[0] != 1:
        raise ValueError(f"Expected features shape [1, 128, T], got {features.shape}")
    
    # Calculate chunk size in frames
    chunk_frames = int(chunk_size_seconds * SAMPLE_RATE / HOP_LENGTH)
    total_frames = features.shape[2]
    
    if total_frames <= chunk_frames:
        return [features]
    
    chunks = []
    start = 0
    while start < total_frames:
        end = min(start + chunk_frames, total_frames)
        chunk = features[:, :, start:end]
        chunks.append(chunk)
        start += chunk_frames
    
    print(f"Split {total_frames} frames into {len(chunks)} chunks")
    return chunks


def validate_audio_file(audio_path: str) -> tuple[bool, str]:
    """
    Validate that audio file can be processed
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        tuple: (is_valid, message)
    """
    try:
        if not Path(audio_path).exists():
            return False, "File does not exist"
        
        # Try to load audio info without full loading
        try:
            info = librosa.get_duration(path=audio_path)
            if info < MIN_RECORDING_LENGTH:
                return False, f"Audio too short: {info:.1f}s (minimum {MIN_RECORDING_LENGTH}s)"
        except Exception:
            # If we can't get duration, try loading the file
            audio, sr = librosa.load(audio_path, sr=None, duration=1.0)  # Load just 1 second
            if len(audio) == 0:
                return False, "Audio file appears to be empty"
        
        return True, "Audio file is valid"
        
    except Exception as e:
        return False, f"Audio validation error: {str(e)}"


# Utility function for debugging
def print_audio_info(audio_path: str):
    """Print detailed information about an audio file"""
    try:
        duration = librosa.get_duration(path=audio_path)
        sr = librosa.get_samplerate(audio_path)
        
        print(f"🎵 Audio Info for {Path(audio_path).name}:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Sample Rate: {sr} Hz")
        print(f"   Expected frames: {int(duration * SAMPLE_RATE / HOP_LENGTH)}")
        print(f"   Min length check: {'✅' if duration >= MIN_RECORDING_LENGTH else '❌'}")
        
    except Exception as e:
        print(f"❌ Error reading audio info: {e}")