#!/usr/bin/env python3
"""
Simplified MAESTRO analysis - process AI prediction only
"""
import numpy as np
import torch
import os
import sys

# Add backend to path
sys.path.append('/Users/kev/360_website/backend')

from models.piano_transcription import load_model
from services.midi_generator import predictions_to_midi

def midi_to_wav_advanced(midi_path, wav_path, sample_rate=44100):
    """Convert MIDI to WAV with good synthesis"""
    try:
        import pretty_midi
        import soundfile as sf
        
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        duration = midi_data.get_end_time()
        total_notes = sum(len(inst.notes) for inst in midi_data.instruments)
        
        if total_notes == 0:
            return False
        
        # Create audio
        audio_length = int(duration * sample_rate)
        audio = np.zeros(audio_length)
        
        for instrument in midi_data.instruments:
            for note in instrument.notes:
                freq = 440 * (2 ** ((note.pitch - 69) / 12))
                start_sample = int(note.start * sample_rate)
                end_sample = int(note.end * sample_rate)
                
                if end_sample > len(audio) or start_sample >= len(audio):
                    continue
                
                note_length = end_sample - start_sample
                if note_length <= 0:
                    continue
                
                t = np.linspace(0, note_length / sample_rate, note_length)
                
                # Simple envelope
                envelope = np.ones(note_length)
                attack = min(int(0.02 * sample_rate), note_length // 3)
                release = min(int(0.1 * sample_rate), note_length // 3)
                
                if attack > 0:
                    envelope[:attack] = np.linspace(0, 1, attack)
                if release > 0:
                    envelope[-release:] = np.linspace(1, 0, release)
                
                # Generate sound
                velocity_scale = note.velocity / 127.0
                fundamental = 0.6 * np.sin(2 * np.pi * freq * t)
                harmonic2 = 0.3 * np.sin(2 * np.pi * freq * 2 * t)
                harmonic3 = 0.1 * np.sin(2 * np.pi * freq * 3 * t)
                
                note_wave = velocity_scale * 0.15 * envelope * (fundamental + harmonic2 + harmonic3)
                audio[start_sample:end_sample] += note_wave
        
        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.8
        
        sf.write(wav_path, audio, sample_rate)
        return True
        
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        return False

def analyze_maestro_prediction():
    """Generate AI prediction and audio from MAESTRO sample"""
    
    print("🎼 MAESTRO Sample 0 - AI Prediction Analysis")
    print("=" * 60)
    
    # Load sample features
    sample_data = np.load('/Users/kev/360_website/maestro_sample_0_full.npz', allow_pickle=True)
    features = sample_data['audio']  # Mel spectrogram features (312, 128)
    
    print(f"📊 Features shape: {features.shape} (time, mels)")
    print(f"📊 Duration: ~{features.shape[0] * 512 / 16000:.1f} seconds")
    
    output_dir = "/Users/kev/360_website/maestro_analysis"
    
    # Load trained model
    print(f"\n🤖 Loading trained model...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = load_model('/Users/kev/360_website/backend/weights/piano_transcription_weights.pth', device)
    
    # Run inference
    print(f"🧠 Running model inference...")
    model.eval()
    with torch.no_grad():
        features_tensor = torch.FloatTensor(features.T).unsqueeze(0).to(device)  # (1, 128, time)
        predictions = model(features_tensor)
        predictions = torch.sigmoid(predictions).cpu().numpy().squeeze()  # (88, time)
    
    # Analyze predictions at different thresholds
    print(f"\n🎹 Note predictions at different thresholds:")
    thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
    for thresh in thresholds:
        note_count = (predictions > thresh).sum()
        print(f"   Threshold {thresh}: {note_count:,} activations")
    
    # Generate MIDI
    print(f"\n🎵 Generating MIDI...")
    midi_path = os.path.join(output_dir, "maestro_sample_0_ai_prediction.mid")
    predictions_tensor = torch.FloatTensor(predictions)
    
    success = predictions_to_midi(predictions_tensor, midi_path, threshold=0.5)
    
    if success:
        print(f"✅ MIDI saved: {midi_path}")
        
        # Convert to audio
        print(f"🔊 Converting to audio...")
        audio_path = os.path.join(output_dir, "maestro_sample_0_ai_prediction.wav")
        
        if midi_to_wav_advanced(midi_path, audio_path):
            print(f"🎧 Audio saved: {audio_path}")
            
            # Get file info
            file_size = os.path.getsize(midi_path)
            print(f"\n📊 Results:")
            print(f"   🎼 MIDI file: {file_size:,} bytes")
            print(f"   🎧 Audio file: maestro_sample_0_ai_prediction.wav")
            print(f"   📁 Location: {output_dir}/")
            
            print(f"\n💡 This transcription comes from the exact MAESTRO sample")
            print(f"   that the model was trained on, so it should be very accurate!")
            
        else:
            print("❌ Audio conversion failed")
    else:
        print("❌ MIDI generation failed")

if __name__ == "__main__":
    analyze_maestro_prediction()