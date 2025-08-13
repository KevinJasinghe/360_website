#!/usr/bin/env python3
"""
Simple test script to verify the application structure is correct.
Run this to check if all files are in place before deployment.
"""

import os
import sys

def check_file(path, description):
    """Check if a file exists and print status"""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ MISSING {description}: {path}")
        return False

def check_directory(path, description):
    """Check if a directory exists and print status"""
    if os.path.isdir(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ MISSING {description}: {path}")
        return False

def main():
    print("🔍 Checking Audio to Sheet Music Application Structure...\n")
    
    all_good = True
    
    # Backend files
    print("Backend Files:")
    all_good &= check_file("backend/app.py", "Main Flask app")
    all_good &= check_file("backend/requirements.txt", "Python requirements")
    all_good &= check_directory("backend/routes", "Routes directory")
    all_good &= check_directory("backend/services", "Services directory")
    all_good &= check_directory("backend/uploads", "Uploads directory")
    
    # Backend route files
    all_good &= check_file("backend/routes/upload.py", "Upload routes")
    all_good &= check_file("backend/routes/youtube.py", "YouTube routes")
    all_good &= check_file("backend/routes/process.py", "Process routes")
    
    # Backend service files
    all_good &= check_file("backend/services/file_converter.py", "File converter service")
    all_good &= check_file("backend/services/youtube_downloader.py", "YouTube downloader")
    all_good &= check_file("backend/services/ai_processor.py", "AI processor")
    all_good &= check_file("backend/services/audio_utils.py", "Audio utilities")
    
    print("\nFrontend Files:")
    all_good &= check_file("frontend/package.json", "React package.json")
    all_good &= check_file("frontend/src/App.js", "React main app")
    all_good &= check_file("frontend/src/index.js", "React index")
    all_good &= check_directory("frontend/src/components", "React components directory")
    all_good &= check_directory("frontend/public", "React public directory")
    
    # Frontend components
    all_good &= check_file("frontend/src/components/FileUpload.js", "File upload component")
    all_good &= check_file("frontend/src/components/YouTubeInput.js", "YouTube input component")
    all_good &= check_file("frontend/src/components/ProgressBar.js", "Progress bar component")
    all_good &= check_file("frontend/src/components/ResultDisplay.js", "Result display component")
    
    print("\nDeployment Files:")
    all_good &= check_file("Dockerfile", "Docker configuration")
    all_good &= check_file("docker-compose.yml", "Docker Compose configuration")
    all_good &= check_file(".dockerignore", "Docker ignore file")
    all_good &= check_file(".gitignore", "Git ignore file")
    all_good &= check_file("README.md", "Documentation")
    
    print("\n" + "="*50)
    
    if all_good:
        print("🎉 SUCCESS! All files are in place.")
        print("\nNext steps:")
        print("1. Install Python dependencies: cd backend && pip install -r requirements.txt")
        print("2. Install Node.js dependencies: cd frontend && npm install")
        print("3. Install FFmpeg on your system")
        print("4. Replace the AI placeholder in backend/services/ai_processor.py with your actual model")
        print("5. Start development: Run 'python backend/app.py' and 'npm start' in frontend/")
        print("6. Or use Docker: 'docker-compose up --build'")
    else:
        print("❌ ISSUES FOUND! Some files are missing.")
        print("Please ensure all files are created correctly.")
        sys.exit(1)

if __name__ == "__main__":
    main()