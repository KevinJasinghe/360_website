"""
MIDI Generation from Piano Roll Predictions
Converts model output to MIDI files using pretty_midi
"""

import numpy as np
import torch
import pretty_midi
from typing import Optional


# Constants from training notebook
MIN_MIDI_NOTE = 21   # A0
MAX_MIDI_NOTE = 108  # C8
SAMPLE_RATE = 16000
HOP_LENGTH = 512


def predictions_to_midi(predictions: torch.Tensor, 
                       output_path: str,
                       threshold: float = 0.5,
                       velocity: int = 64,
                       tempo: float = 120.0) -> bool:
    """
    Convert piano roll predictions to MIDI file
    
    Args:
        predictions: Model output tensor [1, 88, T] or [88, T] 
        output_path: Path to save MIDI file
        threshold: Probability threshold for note detection (0.5)
        velocity: MIDI velocity for all notes (64)
        tempo: Tempo in BPM (120)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Handle batch dimension
        if predictions.dim() == 3:
            predictions = predictions.squeeze(0)  # [88, T]
        elif predictions.dim() != 2:
            raise ValueError(f"Expected predictions shape [88, T] or [1, 88, T], got {predictions.shape}")
        
        # Convert to numpy and apply sigmoid + threshold
        if isinstance(predictions, torch.Tensor):
            probs = torch.sigmoid(predictions).cpu().numpy()
        else:
            probs = predictions
            
        binary_piano_roll = (probs > threshold).astype(bool)
        
        # Create MIDI object
        midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
        piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
        piano = pretty_midi.Instrument(program=piano_program)
        
        # Convert frame times to seconds
        frame_rate = SAMPLE_RATE / HOP_LENGTH  # frames per second
        frame_duration = 1.0 / frame_rate  # seconds per frame
        
        # Extract notes for each piano key
        for key_idx in range(binary_piano_roll.shape[0]):
            midi_note = MIN_MIDI_NOTE + key_idx
            key_activations = binary_piano_roll[key_idx, :]
            
            # Find note onset and offset times
            note_events = extract_note_events(key_activations)
            
            for start_frame, end_frame in note_events:
                start_time = start_frame * frame_duration
                end_time = end_frame * frame_duration
                
                # Create MIDI note
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=midi_note,
                    start=start_time,
                    end=end_time
                )
                piano.notes.append(note)
        
        # Add instrument to MIDI
        midi.instruments.append(piano)
        
        # Save MIDI file
        midi.write(output_path)
        
        print(f"✅ MIDI saved: {len(piano.notes)} notes, {midi.get_end_time():.1f}s duration")
        return True
        
    except Exception as e:
        print(f"❌ MIDI generation failed: {e}")
        return False


def extract_note_events(activations: np.ndarray, min_duration_frames: int = 3) -> list[tuple[int, int]]:
    """
    Extract note start/end events from binary activations
    
    Args:
        activations: Binary array indicating note activity [T]
        min_duration_frames: Minimum note duration in frames
        
    Returns:
        List of (start_frame, end_frame) tuples
    """
    if len(activations) == 0:
        return []
    
    # Find transitions
    diff = np.diff(activations.astype(int))
    onsets = np.where(diff == 1)[0] + 1  # Note starts
    offsets = np.where(diff == -1)[0] + 1  # Note ends
    
    # Handle edge cases
    if activations[0]:
        onsets = np.concatenate([[0], onsets])
    if activations[-1]:
        offsets = np.concatenate([offsets, [len(activations)]])
    
    # Pair onsets with offsets
    events = []
    for i in range(min(len(onsets), len(offsets))):
        start = onsets[i]
        end = offsets[i]
        
        # Filter out very short notes
        if end - start >= min_duration_frames:
            events.append((start, end))
    
    return events


def enhance_predictions(predictions: torch.Tensor, 
                       smoothing_window: int = 3,
                       min_gap_frames: int = 2) -> torch.Tensor:
    """
    Post-process predictions to improve MIDI quality
    
    Args:
        predictions: Raw model predictions [88, T]
        smoothing_window: Window size for temporal smoothing
        min_gap_frames: Minimum gap between same notes
        
    Returns:
        Enhanced predictions tensor
    """
    try:
        # Apply sigmoid to get probabilities
        probs = torch.sigmoid(predictions)
        
        # Temporal smoothing with moving average
        if smoothing_window > 1:
            # Pad for convolution
            padding = smoothing_window // 2
            kernel = torch.ones(1, 1, smoothing_window) / smoothing_window
            
            # Apply 1D convolution along time dimension
            probs_padded = torch.nn.functional.pad(probs.unsqueeze(0), (padding, padding), mode='reflect')
            probs_smooth = torch.nn.functional.conv1d(probs_padded, kernel, groups=1)
            probs = probs_smooth.squeeze(0)
        
        return probs
        
    except Exception as e:
        print(f"Warning: Prediction enhancement failed: {e}")
        return torch.sigmoid(predictions)


def create_test_midi(output_path: str, duration_seconds: float = 5.0) -> bool:
    """
    Create a test MIDI file with a simple melody
    Useful for testing the pipeline without a trained model
    
    Args:
        output_path: Path to save test MIDI
        duration_seconds: Length of test melody
        
    Returns:
        bool: True if successful
    """
    try:
        midi = pretty_midi.PrettyMIDI(initial_tempo=120.0)
        piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
        piano = pretty_midi.Instrument(program=piano_program)
        
        # Create a simple C major scale
        c_major = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 to C5
        note_duration = duration_seconds / len(c_major)
        
        for i, pitch in enumerate(c_major):
            start_time = i * note_duration
            end_time = start_time + note_duration * 0.8  # Small gap between notes
            
            note = pretty_midi.Note(
                velocity=80,
                pitch=pitch,
                start=start_time,
                end=end_time
            )
            piano.notes.append(note)
        
        midi.instruments.append(piano)
        midi.write(output_path)
        
        print(f"✅ Test MIDI created: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Test MIDI creation failed: {e}")
        return False


def analyze_predictions(predictions: torch.Tensor, threshold: float = 0.5) -> dict:
    """
    Analyze model predictions for debugging
    
    Args:
        predictions: Model output [88, T] 
        threshold: Detection threshold
        
    Returns:
        Dictionary with analysis results
    """
    try:
        if predictions.dim() == 3:
            predictions = predictions.squeeze(0)
            
        probs = torch.sigmoid(predictions)
        binary = (probs > threshold)
        
        analysis = {
            'shape': tuple(predictions.shape),
            'total_frames': predictions.shape[1] if predictions.dim() == 2 else 0,
            'duration_seconds': predictions.shape[1] * HOP_LENGTH / SAMPLE_RATE if predictions.dim() == 2 else 0,
            'active_frames': binary.sum().item(),
            'active_keys': (binary.sum(dim=1) > 0).sum().item(),
            'max_prob': probs.max().item(),
            'min_prob': probs.min().item(),
            'mean_prob': probs.mean().item(),
        }
        
        # Find most active keys
        key_activity = binary.sum(dim=1)
        top_keys = torch.topk(key_activity, k=min(5, len(key_activity)))
        
        analysis['top_active_keys'] = [
            {
                'key_index': idx.item(),
                'midi_note': MIN_MIDI_NOTE + idx.item(),
                'frames_active': count.item()
            }
            for idx, count in zip(top_keys.indices, top_keys.values)
            if count > 0
        ]
        
        return analysis
        
    except Exception as e:
        print(f"❌ Prediction analysis failed: {e}")
        return {'error': str(e)}