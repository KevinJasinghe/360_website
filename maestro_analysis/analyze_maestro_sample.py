#!/usr/bin/env python3
"""
Complete analysis of MAESTRO sample_0:
1. Generate original audio from features (if possible)
2. Extract ground truth MIDI labels
3. Run AI model prediction
4. Convert everything to audio for comparison
"""
import numpy as np
import torch
import os
import sys
import pretty_midi
import soundfile as sf

# Add backend to path
sys.path.append('/Users/kev/360_website/backend')

from models.piano_transcription import load_model
from services.midi_generator import predictions_to_midi

def midi_to_wav_advanced(midi_path, wav_path, sample_rate=44100):
    """Convert MIDI to WAV with good synthesis"""
    try:
        print(f"🎼 Processing: {os.path.basename(midi_path)}")
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        
        duration = midi_data.get_end_time()
        total_notes = sum(len(inst.notes) for inst in midi_data.instruments)
        print(f"📊 Duration: {duration:.2f}s, Notes: {total_notes}")
        
        if not midi_data.instruments or total_notes == 0:
            print("❌ No notes found")
            return False
        
        # Create audio
        audio_length = int(duration * sample_rate)
        audio = np.zeros(audio_length)
        
        for instrument in midi_data.instruments:
            for note in instrument.notes:
                freq = 440 * (2 ** ((note.pitch - 69) / 12))
                start_sample = int(note.start * sample_rate)
                end_sample = int(note.end * sample_rate)
                
                if end_sample > len(audio):
                    end_sample = len(audio)
                if start_sample >= len(audio):
                    continue
                
                note_length = end_sample - start_sample
                if note_length <= 0:
                    continue
                
                t = np.linspace(0, note_length / sample_rate, note_length)
                
                # ADSR envelope
                envelope = np.ones(note_length)
                attack_samples = min(int(0.02 * sample_rate), note_length // 3)
                release_samples = min(int(0.1 * sample_rate), note_length // 3)
                
                if attack_samples > 0:
                    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
                if release_samples > 0:
                    envelope[-release_samples:] = np.linspace(1, 0, release_samples)
                
                # Rich harmonics
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
        print(f"✅ Saved: {wav_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def analyze_maestro_sample():
    """Complete analysis pipeline"""
    
    print("🎼 MAESTRO Sample 0 - Complete Analysis")
    print("=" * 70)
    
    # Load sample data
    print("📂 Loading MAESTRO sample...")
    sample_data = np.load('/Users/kev/360_website/maestro_sample_0_full.npz', allow_pickle=True)
    features = sample_data['audio']  # Mel spectrogram features
    ground_truth = sample_data['label']  # Ground truth piano roll
    
    print(f"📊 Features shape: {features.shape} (time, mels)")
    print(f"📊 Ground truth shape: {ground_truth.shape} (time, notes)")
    
    output_dir = "/Users/kev/360_website/maestro_analysis"
    
    # 1. ORIGINAL AUDIO RECONSTRUCTION
    print(f"\n🎵 Step 1: Attempting to reconstruct original audio...")
    print("❌ Cannot reconstruct original audio from mel spectrogram features")
    print("   (Mel spectrograms are lossy - phase information is lost)")
    
    # 2. GROUND TRUTH MIDI
    print(f"\n🎼 Step 2: Converting ground truth labels to MIDI...")
    ground_truth_midi = os.path.join(output_dir, "sample_0_ground_truth.mid")
    
    # Convert ground truth to MIDI
    ground_truth_tensor = torch.FloatTensor(ground_truth.T)  # (88, time)
    gt_success = predictions_to_midi(ground_truth_tensor, ground_truth_midi, threshold=0.5)
    
    if gt_success:
        print(f"✅ Ground truth MIDI saved: {ground_truth_midi}")
        
        # Convert to audio
        gt_audio_path = os.path.join(output_dir, "sample_0_ground_truth.wav")
        if midi_to_wav_advanced(ground_truth_midi, gt_audio_path):
            print(f"🎧 Ground truth audio: {gt_audio_path}")
    else:
        print("❌ Ground truth MIDI generation failed")
    
    # 3. AI MODEL PREDICTION
    print(f"\n🤖 Step 3: Running AI model prediction...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = load_model('/Users/kev/360_website/backend/weights/piano_transcription_weights.pth', device)
    
    model.eval()
    with torch.no_grad():
        features_tensor = torch.FloatTensor(features.T).unsqueeze(0).to(device)  # (1, 128, time)
        predictions = model(features_tensor)
        predictions = torch.sigmoid(predictions).cpu().numpy().squeeze()  # (88, time)
    
    print(f"📊 Predictions shape: {predictions.shape}")
    
    # Generate AI prediction MIDI
    ai_midi_path = os.path.join(output_dir, "sample_0_ai_prediction.mid")
    predictions_tensor = torch.FloatTensor(predictions)
    ai_success = predictions_to_midi(predictions_tensor, ai_midi_path, threshold=0.5)
    
    if ai_success:
        print(f"✅ AI prediction MIDI saved: {ai_midi_path}")
        
        # Convert to audio
        ai_audio_path = os.path.join(output_dir, "sample_0_ai_prediction.wav")
        if midi_to_wav_advanced(ai_midi_path, ai_audio_path):
            print(f"🎧 AI prediction audio: {ai_audio_path}")
    
    # 4. COMPARISON ANALYSIS
    if gt_success and ai_success:
        print(f"\n📊 Step 4: Comparison Analysis...")
        
        # Load and compare MIDIs
        gt_midi_data = pretty_midi.PrettyMIDI(ground_truth_midi)
        ai_midi_data = pretty_midi.PrettyMIDI(ai_midi_path)
        
        gt_notes = sum(len(inst.notes) for inst in gt_midi_data.instruments)
        ai_notes = sum(len(inst.notes) for inst in ai_midi_data.instruments)
        
        print(f"   🎯 Ground Truth: {gt_notes} notes")
        print(f"   🤖 AI Prediction: {ai_notes} notes")
        print(f"   📈 Note difference: {abs(gt_notes - ai_notes)} ({abs(gt_notes - ai_notes)/gt_notes*100:.1f}%)")
        
        # Calculate accuracy at frame level
        gt_binary = (ground_truth > 0.5).astype(float)
        pred_binary = (predictions.T > 0.5).astype(float)
        
        if gt_binary.shape == pred_binary.shape:
            accuracy = np.mean(gt_binary == pred_binary)
            print(f"   🎯 Frame-level accuracy: {accuracy*100:.2f}%")
        
    print(f"\n🎉 Analysis Complete!")
    print(f"📁 All files saved to: {output_dir}/")
    print(f"🎧 Audio files available for listening:")
    
    if gt_success:
        print(f"   🎯 Ground truth: sample_0_ground_truth.wav")
    if ai_success:
        print(f"   🤖 AI prediction: sample_0_ai_prediction.wav")
    
    print(f"\n💡 Since the model was trained on this exact sample,")
    print(f"   the AI prediction should be very close to ground truth!")

if __name__ == "__main__":
    analyze_maestro_sample()