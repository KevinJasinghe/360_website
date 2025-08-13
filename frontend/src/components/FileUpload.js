import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import './FileUpload.css';

const FileUpload = ({ onProcessStart }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError('');
    
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0].code === 'file-too-large') {
        setError('File too large. Maximum size is 1GB.');
      } else if (rejection.errors[0].code === 'file-invalid-type') {
        setError('Invalid file type. Please upload audio or video files.');
      } else {
        setError('File rejected: ' + rejection.errors[0].message);
      }
      return;
    }
    
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    maxSize: 1024 * 1024 * 1024, // 1GB
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'],
      'video/*': ['.mp4', '.avi', '.mov', '.webm', '.mkv']
    }
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError('');
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        },
      });

      if (response.data.upload_id) {
        // Start processing
        onProcessStart(response.data.upload_id);
      }
    } catch (error) {
      console.error('Upload error:', error);
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else if (error.code === 'NETWORK_ERROR') {
        setError('Network error. Please check if the backend server is running.');
      } else {
        setError('Upload failed: ' + error.message);
      }
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError('');
  };

  return (
    <div className="file-upload-container">
      <div className="file-upload-info">
        <h3>Upload Audio or Video File</h3>
        <p>Supported formats: MP3, WAV, MP4, AVI, MOV, M4A, FLAC, OGG, WebM, MKV</p>
        <p>Maximum file size: 1GB</p>
      </div>

      {!file && (
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="dropzone-content">
            <div className="upload-icon">📁</div>
            {isDragActive ? (
              <p>Drop the file here...</p>
            ) : (
              <>
                <p>Drag and drop a file here, or <strong>click to select</strong></p>
                <button type="button" className="btn btn-secondary">
                  Choose File
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {file && (
        <div className="file-info">
          <div className="file-details">
            <div className="file-icon">
              {file.type.startsWith('audio/') ? '🎵' : '🎬'}
            </div>
            <div className="file-metadata">
              <h4>{file.name}</h4>
              <p>{formatFileSize(file.size)}</p>
              <p className="file-type">{file.type || 'Unknown type'}</p>
            </div>
            <button
              type="button"
              className="remove-file-btn"
              onClick={handleRemoveFile}
              disabled={uploading}
            >
              ❌
            </button>
          </div>

          {uploading && (
            <div className="upload-progress">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p>Uploading... {uploadProgress}%</p>
            </div>
          )}

          <div className="upload-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? 'Uploading...' : '🚀 Upload & Process'}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <span>❌ {error}</span>
        </div>
      )}
    </div>
  );
};

export default FileUpload;