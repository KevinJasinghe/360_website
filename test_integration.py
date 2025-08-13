#!/usr/bin/env python3
"""
Test script to verify the model integration works
"""

import sys
import os
import numpy as np
import torch

# Add backend to path
sys.path.append('backend')

def test_model_creation():
    """Test that we can create the model"""
    print("🧪 Testing model creation...")
    try:
        from models.piano_transcription import create_model
        model = create_model(device='cpu')
        print(f"✅ Model created: {model.name}, {sum(p.numel() for p in model.parameters()):,} parameters")
        return model
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return None

def test_audio_processing():
    """Test that we can process audio (with dummy data)"""
    print("\n🧪 Testing audio processing...")
    try:
        from services.audio_processor import extract_audio_features
        
        # Create dummy audio (5 seconds at 16kHz)
        dummy_audio = np.random.randn(5 * 16000).astype(np.float32)
        features = extract_audio_features(dummy_audio, 16000)
        
        if features is not None:
            print(f"✅ Audio processing works: {features.shape}")
            return features
        else:
            print("❌ Audio processing returned None")
            return None
    except Exception as e:
        print(f"❌ Audio processing failed: {e}")
        return None

def test_model_inference():
    """Test that we can run model inference"""
    print("\n🧪 Testing model inference...")
    try:
        model = test_model_creation()
        if model is None:
            return False
        
        # Create dummy input: [1, 128, 312] (batch=1, mels=128, time=312)
        dummy_input = torch.randn(1, 128, 312)
        
        with torch.no_grad():
            output = model(dummy_input)
        
        print(f"✅ Model inference works: input {dummy_input.shape} -> output {output.shape}")
        return output
    except Exception as e:
        print(f"❌ Model inference failed: {e}")
        return None

def test_midi_generation():
    """Test that we can generate MIDI from predictions"""
    print("\n🧪 Testing MIDI generation...")
    try:
        from services.midi_generator import create_test_midi, predictions_to_midi
        
        # Test 1: Create a simple test MIDI
        test_path = "/tmp/test_melody.mid"
        success = create_test_midi(test_path)
        if success:
            print("✅ Test MIDI creation works")
        else:
            print("❌ Test MIDI creation failed")
            return False
        
        # Test 2: Convert dummy predictions to MIDI
        dummy_predictions = torch.sigmoid(torch.randn(1, 88, 312))  # Random probabilities
        prediction_path = "/tmp/test_predictions.mid"
        success = predictions_to_midi(dummy_predictions, prediction_path)
        if success:
            print("✅ Prediction to MIDI conversion works")
            return True
        else:
            print("❌ Prediction to MIDI conversion failed")
            return False
            
    except Exception as e:
        print(f"❌ MIDI generation failed: {e}")
        return False

def test_ai_processor():
    """Test the full AIProcessor pipeline"""
    print("\n🧪 Testing AIProcessor initialization...")
    try:
        from services.ai_processor import AIProcessor
        
        # Test initialization
        success = AIProcessor.initialize()
        if success:
            print("✅ AIProcessor initialized successfully")
            
            # Test model info
            info = AIProcessor.get_model_info()
            print(f"📊 Model info: {info}")
            
            # Test demo MIDI creation
            demo_path = "/tmp/demo.mid"
            success, message = AIProcessor.create_demo_midi(demo_path)
            if success:
                print(f"✅ Demo MIDI: {message}")
            else:
                print(f"❌ Demo MIDI failed: {message}")
            
            return True
        else:
            print("❌ AIProcessor initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ AIProcessor test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting integration tests...")
    print("=" * 60)
    
    # Test individual components
    tests = [
        test_model_creation,
        test_audio_processing, 
        test_model_inference,
        test_midi_generation,
        test_ai_processor
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result is not None and result is not False)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results:")
    test_names = [test.__name__ for test in tests]
    for name, result in zip(test_names, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {name}")
    
    passed = sum(results)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Integration is ready.")
        print("\n📝 Next steps:")
        print("1. Install dependencies: pip install -r backend/requirements.txt")
        print("2. Run the Flask server: python backend/app.py")  
        print("3. Train model in Colab and download weights")
        print("4. Test with real audio files!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())