import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import YouTubeInput from './components/YouTubeInput';
import ProgressBar from './components/ProgressBar';
import ResultDisplay from './components/ResultDisplay';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [processId, setProcessId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);

  const handleProcessStart = (id) => {
    setProcessId(id);
    setIsProcessing(true);
    setResult(null);
  };

  const handleProcessComplete = (resultData) => {
    setIsProcessing(false);
    setResult(resultData);
  };

  const handleReset = () => {
    setProcessId(null);
    setIsProcessing(false);
    setResult(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎵 Audio to Sheet Music Converter</h1>
        <p>Upload audio/video files or YouTube links to generate MIDI sheet music</p>
      </header>

      <main className="App-main">
        {!processId && (
          <div className="tabs-container">
            <div className="tabs">
              <button
                className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
                onClick={() => setActiveTab('upload')}
              >
                📁 Upload File
              </button>
              <button
                className={`tab ${activeTab === 'youtube' ? 'active' : ''}`}
                onClick={() => setActiveTab('youtube')}
              >
                📺 YouTube Link
              </button>
            </div>

            <div className="tab-content">
              {activeTab === 'upload' && (
                <FileUpload onProcessStart={handleProcessStart} />
              )}
              {activeTab === 'youtube' && (
                <YouTubeInput onProcessStart={handleProcessStart} />
              )}
            </div>
          </div>
        )}

        {processId && isProcessing && (
          <ProgressBar
            processId={processId}
            onComplete={handleProcessComplete}
            onReset={handleReset}
          />
        )}

        {result && (
          <ResultDisplay
            result={result}
            processId={processId}
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="App-footer">
        <p>Convert your favorite audio and video files to sheet music with AI</p>
      </footer>
    </div>
  );
}

export default App;