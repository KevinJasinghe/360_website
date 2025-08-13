# Plan 2: Integrating Piano Transcription Model with Website

## Overview
This plan outlines the integration of the piano transcription model from `training.ipynb` into the existing Flask/React website infrastructure. The goal is to replace the placeholder `AIProcessor` with a fully functional piano transcription system.

## Current State Analysis

### From training.ipynb:
- **Model**: `CRNN_OnsetsAndFrames` - A CNN-LSTM hybrid for piano transcription
- **Input**: Mel spectrograms (128 mel bins, 16kHz sample rate)
- **Output**: Piano roll predictions (88 keys, same time resolution)
- **Data Processing**: Complete audio preprocessing pipeline
- **Training**: MAESTRO dataset with MUSDB augmentation

### From existing website:
- **Backend**: Flask REST API with file upload/YouTube download
- **Frontend**: React UI with progress tracking
- **Current AI**: Placeholder `AIProcessor` that creates dummy MIDI files
- **Infrastructure**: Processing status tracking, file management

## Integration Strategy

### Phase 1: Extract and Clean Model Components

#### 1.1 Create Model Module (`backend/models/piano_transcription.py`)
```python
# Extract from training.ipynb cells 13-14:
- CRNN_OnsetsAndFrames class
- Model architecture with proper inference mode
- Device handling (CPU/GPU)
```

#### 1.2 Create Audio Processing Module (`backend/services/audio_processor.py`)
```python
# Extract from training.ipynb cells 8:
- standardize_audio() function
- extract_audio_features() function 
- Configuration constants (SAMPLE_RATE=16000, N_MELS=128, etc.)
```

#### 1.3 Create MIDI Generation Module (`backend/services/midi_generator.py`)
```python
# New functionality needed:
- Convert piano roll predictions to MIDI
- Handle velocity estimation
- Tempo and timing information
- pretty_midi integration
```

### Phase 2: Replace AIProcessor

#### 2.1 New AIProcessor Implementation
```python
class AIProcessor:
    def __init__(self):
        self.model = None
        self.device = None
        self._load_model()
    
    def _load_model(self):
        # Load pre-trained model weights
        # Handle CPU/GPU device selection
        
    def process_audio_to_midi(self, wav_file_path, output_midi_path):
        # 1. Load and preprocess audio
        # 2. Run model inference
        # 3. Convert predictions to MIDI
        # 4. Save MIDI file
```

#### 2.2 Model Loading Strategy
- **Option A**: Load pre-trained weights from training
- **Option B**: Start with randomly initialized model for testing
- **Option C**: Train minimal model on subset for demo

### Phase 3: Dependencies and Environment

#### 3.1 Required Python Packages
```txt
# Core ML/Audio packages
torch>=1.9.0
librosa>=0.8.0
numpy>=1.20.0
pretty_midi>=0.2.9
soundfile>=0.10.0

# Existing packages (already in use)
flask
flask-restful
flask-cors
```

#### 3.2 System Requirements
- **Memory**: Model inference ~500MB-2GB RAM
- **CPU**: Works on CPU, GPU optional for faster inference
- **Storage**: Model weights ~10-50MB

### Phase 4: Integration Steps

#### 4.1 Backend Integration
1. **Replace** `backend/services/ai_processor.py`
2. **Add** model loading on app startup
3. **Update** processing pipeline in `routes/process.py`
4. **Add** proper error handling for model failures

#### 4.2 Configuration Updates
```python
# app.py additions:
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_PATH = 'models/piano_transcription_weights.pth'
```

#### 4.3 File Structure Changes
```
backend/
├── models/
│   ├── __init__.py
│   └── piano_transcription.py     # CRNN model
├── services/
│   ├── ai_processor.py           # Updated with real model
│   ├── audio_processor.py        # Audio preprocessing
│   └── midi_generator.py         # MIDI creation
└── weights/
    └── model_weights.pth         # Pre-trained weights
```

## Implementation Details

### Model Architecture (from notebook)
```python
# Input:  [Batch, 128, Time] - Mel spectrograms
# Output: [Batch, 88, Time]  - Piano key predictions

class CRNN_OnsetsAndFrames(nn.Module):
    # CNN: 3 conv layers with frequency pooling
    # LSTM: Bidirectional LSTM for temporal modeling  
    # FC: Frame-wise classification to 88 piano keys
```

### Audio Processing Pipeline
```python
# Configuration (from notebook)
SAMPLE_RATE = 16000
N_MELS = 128
N_FFT = 2048
HOP_LENGTH = 512
WINDOW_SIZE_SECONDS = 10.0  # Process in 10-second chunks

# Pipeline:
# 1. Load audio with librosa
# 2. Resample to 16kHz mono
# 3. Normalize volume
# 4. Extract mel spectrogram
# 5. Normalize features
```

### MIDI Generation Strategy
```python
# Convert model output to MIDI:
# 1. Apply sigmoid to get probabilities
# 2. Threshold probabilities (>0.5) to get binary decisions
# 3. Convert frame-wise predictions to note events
# 4. Estimate note velocities
# 5. Create MIDI file with pretty_midi
```

## Potential Issues and Solutions

### Issue 1: Model Size and Memory
- **Problem**: Large model may cause memory issues
- **Solution**: Implement model loading only when needed, process audio in chunks

### Issue 2: Processing Time
- **Problem**: Real-time inference may be slow
- **Solution**: Add progress callbacks, process in background threads

### Issue 3: Model Weights
- **Problem**: No pre-trained weights available yet
- **Solution**: Start with random weights for integration testing, train later

### Issue 4: Audio Format Compatibility  
- **Problem**: Model expects 16kHz mono, users upload various formats
- **Solution**: Existing `FileConverter` handles this, ensure compatibility

## Testing Strategy

### Unit Tests
1. Test audio preprocessing with sample files
2. Test model forward pass with dummy input
3. Test MIDI generation from dummy predictions

### Integration Tests  
1. End-to-end processing with simple audio file
2. Test with various audio formats and lengths
3. Verify MIDI output quality

### Performance Tests
1. Memory usage during inference
2. Processing time for different audio lengths  
3. CPU vs GPU performance comparison

## Deployment Considerations

### Development Environment
- Add model weights to `.gitignore`
- Document model training/weights acquisition process
- Provide sample audio files for testing

### Production Environment
- Model weights storage and loading strategy
- Memory monitoring and optimization
- Error handling and graceful degradation

## Questions for Implementation

1. **Model Weights**: Do you have trained weights, or should we start with random initialization for testing?

2. **Performance Requirements**: What's the acceptable processing time for a 3-minute audio file?

3. **Quality Expectations**: What level of transcription accuracy is needed for the demo?

4. **Model Training**: If we need to train the model, do you have access to the MAESTRO dataset?

5. **Deployment**: Will this run locally or be deployed to a server? Any memory/CPU constraints?

## Next Steps

1. **Extract model components** from notebook to separate Python files
2. **Create minimal working inference pipeline** 
3. **Test integration** with existing Flask app
4. **Add comprehensive error handling**
5. **Optimize for production** deployment

This plan provides a clear path from the research notebook to a production-ready web application while maintaining the existing user interface and backend infrastructure.