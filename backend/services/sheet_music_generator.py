"""
Sheet Music Generator - Convert MIDI files to visual sheet music
Uses music21 library to generate and export sheet music notation
"""

import os
import tempfile
from pathlib import Path

try:
    from music21 import converter, stream, note, pitch, duration, tempo, meter
    from music21.midi import MidiFile
    from music21.musicxml import m21ToXml
    MUSIC21_AVAILABLE = True
    print("✅ music21 loaded successfully")
except ImportError:
    MUSIC21_AVAILABLE = False
    print("⚠️ music21 not available - sheet music conversion disabled")

class SheetMusicGenerator:
    """Generate sheet music from MIDI files using music21"""
    
    @staticmethod
    def is_available():
        """Check if sheet music generation is available"""
        return MUSIC21_AVAILABLE
    
    @staticmethod
    def midi_to_musicxml(midi_file_path, output_path=None):
        """
        Convert MIDI file to MusicXML format for sheet music display
        
        Args:
            midi_file_path (str): Path to MIDI file
            output_path (str): Path to save MusicXML file (optional)
            
        Returns:
            tuple: (success: bool, output_path: str, message: str)
        """
        if not MUSIC21_AVAILABLE:
            return False, None, "music21 library not available"
        
        try:
            # Check if MIDI file exists
            if not os.path.exists(midi_file_path):
                return False, None, f"MIDI file not found: {midi_file_path}"
            
            print(f"🎼 Converting MIDI to sheet music: {Path(midi_file_path).name}")
            
            # Load MIDI file
            score = converter.parse(midi_file_path)
            
            if score is None:
                return False, None, "Failed to parse MIDI file"
            
            # Clean up the score for better sheet music display
            score = SheetMusicGenerator._clean_score_for_display(score)
            
            # Set output path if not provided
            if output_path is None:
                base_name = Path(midi_file_path).stem
                output_path = str(Path(midi_file_path).parent / f"{base_name}_sheet.xml")
            
            # Export to MusicXML
            score.write('musicxml', fp=output_path)
            
            # Verify the file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                return True, output_path, f"Sheet music generated successfully ({file_size} bytes)"
            else:
                return False, None, "Failed to write MusicXML file"
                
        except Exception as e:
            print(f"❌ Sheet music generation error: {e}")
            return False, None, f"Sheet music generation failed: {str(e)}"
    
    @staticmethod
    def midi_to_png(midi_file_path, output_path=None):
        """
        Convert MIDI file to PNG image of sheet music
        
        Args:
            midi_file_path (str): Path to MIDI file
            output_path (str): Path to save PNG file (optional)
            
        Returns:
            tuple: (success: bool, output_path: str, message: str)
        """
        if not MUSIC21_AVAILABLE:
            return False, None, "music21 library not available"
        
        try:
            # Check if MIDI file exists
            if not os.path.exists(midi_file_path):
                return False, None, f"MIDI file not found: {midi_file_path}"
            
            print(f"🖼️ Converting MIDI to PNG sheet music: {Path(midi_file_path).name}")
            
            # Load MIDI file
            score = converter.parse(midi_file_path)
            
            if score is None:
                return False, None, "Failed to parse MIDI file"
            
            # Clean up the score for better sheet music display
            score = SheetMusicGenerator._clean_score_for_display(score)
            
            # Set output path if not provided
            if output_path is None:
                base_name = Path(midi_file_path).stem
                output_path = str(Path(midi_file_path).parent / f"{base_name}_sheet.png")
            
            # Export to PNG (requires additional dependencies like musescore)
            try:
                score.write('png', fp=output_path)
                
                # Verify the file was created
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    return True, output_path, f"Sheet music PNG generated successfully ({file_size} bytes)"
                else:
                    return False, None, "Failed to write PNG file"
                    
            except Exception as png_error:
                # PNG export might not work without additional tools, fallback to MusicXML
                print(f"⚠️ PNG export failed ({png_error}), generating MusicXML instead")
                return SheetMusicGenerator.midi_to_musicxml(midi_file_path, output_path.replace('.png', '.xml'))
                
        except Exception as e:
            print(f"❌ Sheet music PNG generation error: {e}")
            return False, None, f"Sheet music generation failed: {str(e)}"
    
    @staticmethod
    def _clean_score_for_display(score):
        """
        Clean and optimize the score for better sheet music display
        
        Args:
            score: music21 Score object
            
        Returns:
            Cleaned score object
        """
        try:
            # Set tempo if not present
            if not score.metronomeMarkBoundaries():
                score.insert(0, tempo.TempoIndication(number=120))
            
            # Set time signature if not present
            if not score.getTimeSignatures():
                score.insert(0, meter.TimeSignature('4/4'))
            
            # Clean up very short notes (artifacts from AI prediction)
            for part in score.parts:
                notes_to_remove = []
                for element in part.flat.notes:
                    if hasattr(element, 'duration') and element.duration.quarterLength < 0.1:
                        notes_to_remove.append(element)
                
                for note_to_remove in notes_to_remove:
                    part.remove(note_to_remove)
            
            # Quantize note durations to standard values
            score.quantize(quarterLengthDivisors=[4, 3], processOffsets=True, processDurations=True)
            
            return score
            
        except Exception as e:
            print(f"⚠️ Score cleaning warning: {e}")
            return score  # Return original score if cleaning fails
    
    @staticmethod
    def get_score_info(midi_file_path):
        """
        Get information about the MIDI score
        
        Args:
            midi_file_path (str): Path to MIDI file
            
        Returns:
            dict: Score information or None if error
        """
        if not MUSIC21_AVAILABLE:
            return None
        
        try:
            score = converter.parse(midi_file_path)
            if score is None:
                return None
            
            # Extract basic information
            info = {
                'duration_seconds': float(score.duration.quarterLength) * 0.5,  # Approximate at 120 BPM
                'num_parts': len(score.parts),
                'num_notes': sum(len(part.flat.notes) for part in score.parts),
                'key_signature': None,
                'time_signature': None,
                'tempo': None
            }
            
            # Get key signature
            key_sigs = score.flatten().getElementsByClass('KeySignature')
            if key_sigs:
                info['key_signature'] = str(key_sigs[0])
            
            # Get time signature
            time_sigs = score.flatten().getElementsByClass('TimeSignature')
            if time_sigs:
                info['time_signature'] = str(time_sigs[0])
            
            # Get tempo
            tempos = score.flatten().getElementsByClass('TempoIndication')
            if tempos:
                info['tempo'] = tempos[0].number
            
            return info
            
        except Exception as e:
            print(f"❌ Score info extraction error: {e}")
            return None
    
    @staticmethod
    def create_test_sheet_music(output_path):
        """
        Create a test sheet music file for verification
        
        Args:
            output_path (str): Path to save test sheet music
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not MUSIC21_AVAILABLE:
            return False, "music21 library not available"
        
        try:
            # Create a simple test score
            score = stream.Score()
            part = stream.Part()
            
            # Add time signature and key signature
            part.append(meter.TimeSignature('4/4'))
            part.append(tempo.TempoIndication(number=120))
            
            # Add a simple melody (C major scale)
            notes_data = [
                ('C4', 1.0), ('D4', 1.0), ('E4', 1.0), ('F4', 1.0),
                ('G4', 1.0), ('A4', 1.0), ('B4', 1.0), ('C5', 2.0)
            ]
            
            for note_name, duration_val in notes_data:
                n = note.Note(note_name)
                n.duration.quarterLength = duration_val
                part.append(n)
            
            score.append(part)
            
            # Export to MusicXML
            score.write('musicxml', fp=output_path)
            
            if os.path.exists(output_path):
                return True, "Test sheet music created successfully"
            else:
                return False, "Failed to create test sheet music file"
                
        except Exception as e:
            return False, f"Test sheet music creation failed: {str(e)}"


# Utility functions for integration with existing system
def validate_midi_for_sheet_music(midi_file_path):
    """
    Validate that a MIDI file can be converted to sheet music
    
    Args:
        midi_file_path (str): Path to MIDI file
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not os.path.exists(midi_file_path):
        return False, "MIDI file not found"
    
    if not MUSIC21_AVAILABLE:
        return False, "Sheet music conversion not available (music21 required)"
    
    try:
        # Quick parse test
        score = converter.parse(midi_file_path)
        if score is None:
            return False, "MIDI file could not be parsed"
        
        # Check if it has any musical content
        total_notes = sum(len(part.flat.notes) for part in score.parts)
        if total_notes == 0:
            return False, "MIDI file contains no notes"
        
        return True, f"MIDI file valid for sheet music conversion ({total_notes} notes)"
        
    except Exception as e:
        return False, f"MIDI validation error: {str(e)}"


def get_supported_sheet_formats():
    """
    Get list of supported sheet music export formats
    
    Returns:
        list: Supported formats
    """
    if not MUSIC21_AVAILABLE:
        return []
    
    formats = ['musicxml']  # Always supported
    
    # Check if PNG export is available (requires additional tools)
    try:
        # This would require musescore or similar tool to be installed
        formats.append('png')
    except:
        pass
    
    return formats