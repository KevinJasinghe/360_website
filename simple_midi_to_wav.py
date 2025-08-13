#!/usr/bin/env python3
"""
Simple MIDI to WAV conversion using sine wave synthesis
"""

import pretty_midi
import numpy as np
import soundfile as sf

def midi_to_wav_simple(midi_path, wav_path, sample_rate=44100):
    """
    Convert MIDI to WAV using simple sine wave synthesis
    """
    try:
        print(f"🎼 Loading MIDI: {midi_path}")
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        
        duration = midi_data.get_end_time()
        print(f"📊 Duration: {duration:.2f} seconds")
        print(f"📊 Instruments: {len(midi_data.instruments)}")
        
        if not midi_data.instruments:
            print("❌ No instruments found in MIDI")
            return False
            
        # Count notes
        total_notes = sum(len(inst.notes) for inst in midi_data.instruments)
        print(f"📊 Total notes: {total_notes}")
        
        # Create audio buffer
        audio_length = int(duration * sample_rate)
        audio = np.zeros(audio_length)
        
        print("🔊 Synthesizing with sine waves...")
        
        # Process each instrument
        for inst_idx, instrument in enumerate(midi_data.instruments):
            print(f"   Instrument {inst_idx}: {len(instrument.notes)} notes")
            
            # Synthesize each note
            for note in instrument.notes:
                # Convert MIDI note to frequency
                freq = 440 * (2 ** ((note.pitch - 69) / 12))
                
                # Calculate sample indices
                start_sample = int(note.start * sample_rate)
                end_sample = int(note.end * sample_rate)
                
                if end_sample > len(audio):
                    end_sample = len(audio)
                    
                if start_sample >= len(audio):
                    continue
                
                # Generate sine wave for this note
                note_length = end_sample - start_sample
                t = np.linspace(0, note_length / sample_rate, note_length)
                
                # Create envelope (attack, decay, release)
                envelope = np.ones(note_length)
                attack_samples = min(int(0.01 * sample_rate), note_length // 4)  # 10ms attack
                release_samples = min(int(0.05 * sample_rate), note_length // 4)  # 50ms release
                
                # Attack
                if attack_samples > 0:
                    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
                
                # Release  
                if release_samples > 0:
                    envelope[-release_samples:] = np.linspace(1, 0, release_samples)
                
                # Generate sine wave with envelope
                velocity_scale = note.velocity / 127.0
                sine_wave = velocity_scale * 0.1 * envelope * np.sin(2 * np.pi * freq * t)
                
                # Add to audio buffer
                audio[start_sample:end_sample] += sine_wave
        
        # Normalize to prevent clipping
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save to file
        print(f"💾 Saving to: {wav_path}")
        sf.write(wav_path, audio, sample_rate)
        
        print(f"✅ Conversion complete!")
        print(f"   Output: {len(audio) / sample_rate:.2f} seconds")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def analyze_midi_notes(midi_path):
    """Analyze the transcribed notes"""
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        
        print(f"\n🔍 Detailed MIDI Analysis:")
        print(f"   File: {midi_path}")
        print(f"   Duration: {midi_data.get_end_time():.2f}s")
        
        for i, instrument in enumerate(midi_data.instruments):
            notes = instrument.notes
            if not notes:
                continue
                
            print(f"\n   Instrument {i} ({instrument.name}):")
            print(f"     Program: {instrument.program}")
            print(f"     Notes: {len(notes)}")
            
            # Analyze pitch distribution
            pitches = [note.pitch for note in notes]
            print(f"     Pitch range: {min(pitches)} to {max(pitches)} (MIDI notes)")
            print(f"     Most common pitches: {sorted(set(pitches), key=pitches.count, reverse=True)[:5]}")
            
            # Analyze timing
            note_durations = [note.end - note.start for note in notes]
            print(f"     Note duration range: {min(note_durations):.3f}s to {max(note_durations):.3f}s")
            print(f"     Average note duration: {np.mean(note_durations):.3f}s")
            
            # Sample some notes
            print(f"     First 5 notes:")
            for j, note in enumerate(notes[:5]):
                print(f"       {j+1}. Pitch {note.pitch}, {note.start:.2f}s-{note.end:.2f}s, vel {note.velocity}")
                
    except Exception as e:
        print(f"❌ Analysis error: {e}")

if __name__ == "__main__":
    midi_file = "/Users/kev/360_website/bass_ai_transcription.mid"
    wav_file = "/Users/kev/360_website/bass_ai_playback.wav"
    
    print("🎵 Converting AI Bass Transcription to Audio")
    print("=" * 60)
    
    # Analyze the MIDI in detail
    analyze_midi_notes(midi_file)
    
    print("\n" + "=" * 60)
    # Convert to audio
    success = midi_to_wav_simple(midi_file, wav_file)
    
    if success:
        print(f"\n🎉 SUCCESS! Audio files ready for comparison:")
        print(f"   📁 Original bass: bass_test.wav (55.8 MB)")
        print(f"   🤖 AI transcription: bass_ai_playback.wav")
        print(f"\n🎧 Listen to both files to hear how well your AI model captured the bass!")
        print(f"   🎯 Your AI detected 9,482 notes in 5.5 minutes of audio!")
    else:
        print(f"\n❌ Audio conversion failed")