import React, { useState } from 'react';
import axios from 'axios';
import './YouTubeInput.css';

const YouTubeInput = ({ onProcessStart }) => {
  const [url, setUrl] = useState('');
  const [videoInfo, setVideoInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const isValidYouTubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)/;
    return youtubeRegex.test(url);
  };

  const handleUrlChange = (e) => {
    const newUrl = e.target.value;
    setUrl(newUrl);
    setError('');
    setVideoInfo(null);
  };

  const handlePreview = async () => {
    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    if (!isValidYouTubeUrl(url)) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/youtube/preview', { url: url.trim() });
      
      if (response.data.video_info) {
        setVideoInfo(response.data);
        if (!response.data.is_valid) {
          setError(response.data.warning || 'Video cannot be processed');
        }
      }
    } catch (error) {
      console.error('Preview error:', error);
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else if (error.code === 'NETWORK_ERROR') {
        setError('Network error. Please check if the backend server is running.');
      } else {
        setError('Failed to get video information: ' + error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async () => {
    if (!videoInfo || !videoInfo.is_valid) {
      setError('Please preview a valid video first');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      const response = await axios.post('/api/youtube', { url: url.trim() });
      
      if (response.data.download_id) {
        onProcessStart(response.data.download_id);
      }
    } catch (error) {
      console.error('Process error:', error);
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else if (error.code === 'NETWORK_ERROR') {
        setError('Network error. Please check if the backend server is running.');
      } else {
        setError('Failed to start processing: ' + error.message);
      }
      setProcessing(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handlePreview();
    }
  };

  return (
    <div className="youtube-input-container">
      <div className="youtube-input-info">
        <h3>YouTube Video Link</h3>
        <p>Enter a YouTube URL to extract audio and convert to sheet music</p>
        <p>Maximum video length: 10 minutes</p>
      </div>

      <div className="url-input-section">
        <div className="input-group">
          <input
            type="url"
            value={url}
            onChange={handleUrlChange}
            onKeyPress={handleKeyPress}
            placeholder="https://www.youtube.com/watch?v=..."
            className="url-input"
            disabled={processing}
          />
          <button
            type="button"
            className="btn btn-secondary preview-btn"
            onClick={handlePreview}
            disabled={loading || processing || !url.trim()}
          >
            {loading ? '🔄' : '🔍'} Preview
          </button>
        </div>

        <div className="url-examples">
          <p><strong>Supported formats:</strong></p>
          <ul>
            <li>https://www.youtube.com/watch?v=VIDEO_ID</li>
            <li>https://youtu.be/VIDEO_ID</li>
            <li>https://youtube.com/embed/VIDEO_ID</li>
          </ul>
        </div>
      </div>

      {videoInfo && (
        <div className={`video-info ${videoInfo.is_valid ? 'valid' : 'invalid'}`}>
          <div className="video-details">
            <div className="video-thumbnail">📺</div>
            <div className="video-metadata">
              <h4>{videoInfo.video_info.title}</h4>
              <p><strong>Duration:</strong> {formatDuration(videoInfo.video_info.duration)} ({videoInfo.video_info.duration}s)</p>
              <p><strong>Uploader:</strong> {videoInfo.video_info.uploader}</p>
              {!videoInfo.is_valid && (
                <p className="warning">⚠️ {videoInfo.warning}</p>
              )}
            </div>
          </div>

          {videoInfo.is_valid && (
            <div className="process-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleProcess}
                disabled={processing}
              >
                {processing ? 'Starting...' : '🚀 Download & Process'}
              </button>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="error-message">
          <span>❌ {error}</span>
        </div>
      )}

      <div className="youtube-tips">
        <h4>💡 Tips:</h4>
        <ul>
          <li>Choose videos with clear audio for best results</li>
          <li>Music videos and performances work best</li>
          <li>Avoid videos with lots of background noise</li>
          <li>The AI works better with instrumental music</li>
        </ul>
      </div>
    </div>
  );
};

export default YouTubeInput;