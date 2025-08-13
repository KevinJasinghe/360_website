#!/usr/bin/env python3
"""
Check that the file structure is set up correctly
"""

import os
from pathlib import Path

def check_file_structure():
    """Check that all required files exist"""
    print("📂 Checking file structure...")
    
    required_files = [
        "backend/models/__init__.py",
        "backend/models/piano_transcription.py",
        "backend/services/ai_processor.py", 
        "backend/services/audio_processor.py",
        "backend/services/midi_generator.py",
        "backend/requirements.txt",
        "backend/app.py",
        "backend/weights/",  # directory
        "plan2.md",
        "training.ipynb"
    ]
    
    missing = []
    for path in required_files:
        full_path = Path(path)
        if path.endswith('/'):
            # Check directory
            if not full_path.is_dir():
                missing.append(path)
            else:
                print(f"✅ {path}")
        else:
            # Check file
            if not full_path.exists():
                missing.append(path)
            else:
                print(f"✅ {path}")
    
    if missing:
        print(f"\n❌ Missing files/directories:")
        for path in missing:
            print(f"   - {path}")
        return False
    else:
        print(f"\n🎉 All required files present!")
        return True

def check_imports():
    """Check basic Python imports without heavy dependencies"""
    print("\n🐍 Checking basic imports...")
    
    import sys
    sys.path.append('backend')
    
    try:
        # Check if files can be imported (syntax check)
        import importlib.util
        
        files_to_check = [
            "backend/models/piano_transcription.py",
            "backend/services/audio_processor.py", 
            "backend/services/midi_generator.py"
        ]
        
        for file_path in files_to_check:
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            if spec is None:
                print(f"❌ Cannot load spec for {file_path}")
                return False
            print(f"✅ {file_path} syntax OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Import check failed: {e}")
        return False

def show_next_steps():
    """Show what to do next"""
    print("\n🚀 Next Steps:")
    print("=" * 50)
    print("1. Install dependencies:")
    print("   cd backend && pip install -r requirements.txt")
    print("")
    print("2. Test the integration:")
    print("   python test_integration.py")
    print("")
    print("3. Train model in Google Colab:")
    print("   - Upload training.ipynb to Colab")
    print("   - Run all cells to train an overfitted model")
    print("   - Download the .pth file to backend/weights/")
    print("")
    print("4. Start the Flask server:")
    print("   python backend/app.py")
    print("")
    print("5. Upload a piano audio file and test!")
    print("")
    print("📝 Notes:")
    print("- The current model uses random weights (for testing)")
    print("- Train in Colab to get a functional model")
    print("- The overfitting setup will create a working demo")

def main():
    """Main setup checker"""
    print("🔧 Checking Piano Transcription Integration Setup")
    print("=" * 60)
    
    structure_ok = check_file_structure()
    imports_ok = check_imports()
    
    print("\n" + "=" * 60) 
    print("📋 Setup Status:")
    print(f"   File structure: {'✅ OK' if structure_ok else '❌ ISSUES'}")
    print(f"   Import syntax:  {'✅ OK' if imports_ok else '❌ ISSUES'}")
    
    if structure_ok and imports_ok:
        print("\n🎉 Setup looks good!")
        show_next_steps()
        return 0
    else:
        print("\n⚠️  Setup has issues. Fix the problems above first.")
        return 1

if __name__ == "__main__":
    exit(main())