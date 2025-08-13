#!/bin/bash

# Audio to Sheet Music Converter - Setup Script
# This script sets up the development environment

echo "🎵 Setting up Audio to Sheet Music Converter..."
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg is not installed. This is required for audio conversion."
    echo "    Please install FFmpeg:"
    echo "    - macOS: brew install ffmpeg"
    echo "    - Ubuntu/Debian: sudo apt install ffmpeg"
    echo "    - Windows: Download from https://ffmpeg.org/download.html"
    echo ""
fi

echo "📦 Installing Python dependencies..."
cd backend
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Python dependencies"
        exit 1
    fi
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ requirements.txt not found in backend/"
    exit 1
fi
cd ..

echo "📦 Installing Node.js dependencies..."
cd frontend
if [ -f "package.json" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Node.js dependencies"
        exit 1
    fi
    echo "✅ Node.js dependencies installed successfully"
else
    echo "❌ package.json not found in frontend/"
    exit 1
fi
cd ..

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Replace the AI model placeholder in backend/services/ai_processor.py"
echo "   with your actual Jupyter notebook code"
echo ""
echo "2. To start development:"
echo "   Terminal 1: cd backend && python3 app.py"
echo "   Terminal 2: cd frontend && npm start"
echo ""
echo "3. Or use Docker:"
echo "   docker-compose up --build"
echo ""
echo "4. Access the application:"
echo "   - Development: http://localhost:3000 (React dev server)"
echo "   - Production: http://localhost:5000 (Flask server)"
echo ""
echo "✨ Happy coding!"