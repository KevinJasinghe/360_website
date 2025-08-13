import os
import torch
from pathlib import Path

# Import our custom modules
from models.piano_transcription import load_model, create_model
from services.audio_processor import process_audio_for_inference, validate_audio_file, chunk_audio_features
from services.midi_generator import predictions_to_midi, create_test_midi, analyze_predictions

class AIProcessor:
    """
    Piano Transcription AI Processor using CRNN model
    Processes audio files and converts them to MIDI sheet music
    """
    
    _model = None
    _device = None
    
    @classmethod
    def initialize(cls, model_path=None, device=None):
        """
        Initialize the AI model
        
        Args:
            model_path: Path to trained model weights (None for random weights)
            device: torch device ('cpu' or 'cuda', None for auto-detect)
        """
        try:
            # Auto-detect device if not specified
            if device is None:
                cls._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            else:
                cls._device = torch.device(device)
            
            print(f"🔧 Initializing AI model on {cls._device}")
            
            # Load or create model
            if model_path and os.path.exists(model_path):
                cls._model = load_model(model_path, device=cls._device)
                print(f"✅ Loaded trained model from {model_path}")
            else:
                cls._model = create_model(device=cls._device)
                if model_path:
                    print(f"⚠️  Model file {model_path} not found, using random weights")
                else:
                    print("📝 Using model with random weights (for testing)")
            
            return True
            
        except Exception as e:
            print(f"❌ Model initialization failed: {e}")
            cls._model = None
            cls._device = None
            return False
    
    @classmethod
    def is_initialized(cls):
        """Check if model is initialized"""
        return cls._model is not None and cls._device is not None
    
    @classmethod
    def process_audio_to_midi(cls, wav_file_path, output_midi_path):
        """
        Process WAV file and convert to MIDI sheet music using the trained model.
        
        Args:
            wav_file_path (str): Path to the WAV file
            output_midi_path (str): Path where MIDI file should be saved
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Check if model is initialized
            if not cls.is_initialized():
                # Try to initialize with default settings
                if not cls.initialize():
                    return False, "Model initialization failed"
            
            # Validate input file
            if not os.path.exists(wav_file_path):
                return False, "WAV file not found"
            
            print(f"🎵 Processing audio: {Path(wav_file_path).name}")
            
            # Step 1: Validate audio file
            is_valid, validation_msg = validate_audio_file(wav_file_path)
            if not is_valid:
                return False, f"Audio validation failed: {validation_msg}"
            
            # Step 2: Process audio to features
            print("🔄 Extracting audio features...")
            features = process_audio_for_inference(wav_file_path)
            if features is None:
                return False, "Audio feature extraction failed"
            
            # Step 3: Run model inference
            print(f"🧠 Running AI model inference on {cls._device}...")
            features = features.to(cls._device)
            
            with torch.no_grad():
                cls._model.eval()
                
                # Handle long audio by chunking
                if features.shape[2] > 1000:  # More than ~20 seconds
                    predictions = cls._process_long_audio(features)
                else:
                    predictions = cls._model(features)  # [1, 88, T]
            
            # Step 4: Analyze predictions for debugging
            analysis = analyze_predictions(predictions)
            print(f"📊 Prediction analysis: {analysis['active_keys']} active keys, "
                  f"{analysis['active_frames']} active frames, "
                  f"max_prob={analysis['max_prob']:.3f}")
            
            # Step 5: Convert to MIDI
            print("🎼 Converting predictions to MIDI...")
            success = predictions_to_midi(predictions, output_midi_path)
            
            if success:
                file_size = os.path.getsize(output_midi_path)
                return True, f"AI processing completed successfully! MIDI file: {file_size} bytes"
            else:
                return False, "MIDI generation failed"
                
        except Exception as e:
            print(f"❌ Processing error: {e}")
            # Fallback: create a test MIDI for debugging
            try:
                print("🔄 Creating fallback test MIDI...")
                create_test_midi(output_midi_path)
                return True, f"AI processing failed, created test MIDI instead: {str(e)}"
            except:
                return False, f"AI processing failed: {str(e)}"
    
    @classmethod
    def _process_long_audio(cls, features):
        """
        Process long audio by chunking and concatenating results
        
        Args:
            features: Audio features tensor [1, 128, T]
            
        Returns:
            predictions: Concatenated predictions [1, 88, T]
        """
        print("📏 Processing long audio in chunks...")
        chunks = chunk_audio_features(features)
        chunk_predictions = []
        
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i+1}/{len(chunks)}: {chunk.shape}")
            chunk_pred = cls._model(chunk)
            chunk_predictions.append(chunk_pred)
        
        # Concatenate along time dimension
        full_predictions = torch.cat(chunk_predictions, dim=2)
        print(f"✅ Processed {len(chunks)} chunks -> {full_predictions.shape}")
        return full_predictions
    
    
    @staticmethod
    def validate_wav_file(wav_file_path):
        """
        Validate that the WAV file can be processed.
        Uses the enhanced validation from audio_processor module.
        
        Args:
            wav_file_path (str): Path to the WAV file
        
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        return validate_audio_file(wav_file_path)
    
    @classmethod
    def get_model_info(cls):
        """
        Get information about the current model
        
        Returns:
            dict: Model information
        """
        if not cls.is_initialized():
            return {'status': 'not_initialized'}
        
        return {
            'status': 'initialized',
            'device': str(cls._device),
            'model_name': cls._model.name if hasattr(cls._model, 'name') else 'CRNN_OnsetsAndFrames',
            'num_parameters': sum(p.numel() for p in cls._model.parameters()),
            'model_size_mb': sum(p.numel() * p.element_size() for p in cls._model.parameters()) / (1024 * 1024)
        }
    
    @classmethod
    def create_demo_midi(cls, output_path):
        """
        Create a demo MIDI file for testing
        
        Args:
            output_path: Path to save demo MIDI
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            success = create_test_midi(output_path, duration_seconds=8.0)
            if success:
                return True, "Demo MIDI created successfully"
            else:
                return False, "Demo MIDI creation failed"
        except Exception as e:
            return False, f"Demo MIDI creation error: {str(e)}"