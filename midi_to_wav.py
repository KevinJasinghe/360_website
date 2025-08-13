#!/usr/bin/env python3
"""
Convert MIDI file to WAV using pretty_midi
"""

import sys
import pretty_midi
import numpy as np
import soundfile as sf

def midi_to_wav(midi_path, wav_path, sample_rate=44100):
    """
    Convert MIDI file to WAV audio
    
    Args:
        midi_path: Path to input MIDI file
        wav_path: Path to output WAV file  
        sample_rate: Sample rate for output audio
    """
    try:
        # Load MIDI file
        print(f"🎼 Loading MIDI: {midi_path}")
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        
        # Get MIDI info
        duration = midi_data.get_end_time()
        print(f"📊 MIDI Duration: {duration:.2f} seconds")
        print(f"📊 Instruments: {len(midi_data.instruments)}")
        
        if midi_data.instruments:
            total_notes = sum(len(inst.notes) for inst in midi_data.instruments)
            print(f"📊 Total Notes: {total_notes}")
        
        # Synthesize audio using pretty_midi's built-in synthesizer
        print(f"🔊 Synthesizing audio at {sample_rate}Hz...")
        audio = midi_data.fluidsynth(fs=sample_rate)
        
        if len(audio) == 0:
            print("❌ No audio generated - MIDI might be empty or invalid")
            return False
            
        # Normalize audio to prevent clipping
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save to WAV
        print(f"💾 Saving WAV: {wav_path}")
        sf.write(wav_path, audio, sample_rate)
        
        # Print stats
        file_size = len(audio) / sample_rate
        print(f"✅ Conversion complete!")
        print(f"   Output duration: {file_size:.2f} seconds")
        print(f"   Sample rate: {sample_rate} Hz")
        print(f"   Audio range: {np.min(audio):.3f} to {np.max(audio):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False

def analyze_midi(midi_path):
    """Analyze MIDI file contents"""
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        
        print(f"\n🔍 MIDI Analysis:")
        print(f"   Duration: {midi_data.get_end_time():.2f}s")
        print(f"   Tempo changes: {len(midi_data.tempo_changes)}")
        
        for i, instrument in enumerate(midi_data.instruments):
            print(f"   Instrument {i}: {instrument.name} (Program {instrument.program})")
            print(f"     Notes: {len(instrument.notes)}")
            
            if instrument.notes:
                pitches = [note.pitch for note in instrument.notes]
                print(f"     Pitch range: {min(pitches)} to {max(pitches)}")
                print(f"     Duration range: {min(note.end - note.start for note in instrument.notes):.3f}s to {max(note.end - note.start for note in instrument.notes):.3f}s")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    midi_file = "/Users/kev/360_website/bass_ai_transcription.mid"
    wav_file = "/Users/kev/360_website/bass_ai_playback.wav"
    
    print("🎵 Converting AI-transcribed MIDI back to audio")
    print("=" * 50)
    
    # Analyze the MIDI first
    analyze_midi(midi_file)
    
    # Convert to WAV
    print("\n" + "=" * 50)
    success = midi_to_wav(midi_file, wav_file)
    
    if success:
        print(f"\n🎉 Success! You can now listen to:")
        print(f"   Original: bass_test.wav (55.8 MB)")
        print(f"   AI transcription: {wav_file}")
        print(f"\n💡 Compare them to see how well your AI model performed!")
    else:
        print(f"\n❌ Conversion failed")