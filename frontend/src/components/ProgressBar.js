import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './ProgressBar.css';

const ProgressBar = ({ processId, onComplete, onReset }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('starting');
  const [message, setMessage] = useState('Initializing...');
  const [error, setError] = useState('');
  const [hasStarted, setHasStarted] = useState(false);

  const pollProgress = useCallback(async () => {
    try {
      const response = await axios.get(`/api/process/${processId}`);
      const data = response.data;
      
      setProgress(data.progress || 0);
      setStatus(data.status);
      setMessage(data.message || 'Processing...');
      
      if (data.status === 'completed') {
        onComplete({
          processId: processId,
          status: data.status,
          message: data.message,
          midiReady: data.midi_ready
        });
        return false; // Stop polling
      } else if (data.status === 'failed') {
        setError(data.message || 'Processing failed');
        return false; // Stop polling
      }
      
      return true; // Continue polling
    } catch (error) {
      console.error('Progress polling error:', error);
      if (error.response?.status === 404) {
        setError('Process not found');
      } else if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError('Failed to get progress: ' + error.message);
      }
      return false; // Stop polling
    }
  }, [processId, onComplete]);

  const startProcessing = useCallback(async () => {
    try {
      const response = await axios.post(`/api/process/${processId}`);
      if (response.data.message) {
        setMessage(response.data.message);
        setHasStarted(true);
      }
    } catch (error) {
      console.error('Start processing error:', error);
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError('Failed to start processing: ' + error.message);
      }
    }
  }, [processId]);

  useEffect(() => {
    if (!hasStarted) {
      startProcessing();
    }

    const pollInterval = setInterval(async () => {
      const shouldContinue = await pollProgress();
      if (!shouldContinue) {
        clearInterval(pollInterval);
      }
    }, 1000); // Poll every second

    return () => {
      clearInterval(pollInterval);
    };
  }, [pollProgress, startProcessing, hasStarted]);

  const getProgressColor = () => {
    if (error) return '#dc3545';
    if (status === 'completed') return '#28a745';
    if (progress < 30) return '#6c757d';
    if (progress < 70) return '#ffc107';
    return '#17a2b8';
  };

  const getStatusIcon = () => {
    if (error) return '❌';
    if (status === 'completed') return '✅';
    if (status === 'processing') return '⚙️';
    return '🔄';
  };

  const getProgressSteps = () => {
    const steps = [
      { threshold: 0, label: 'Starting', icon: '🚀' },
      { threshold: 10, label: 'Downloading/Uploading', icon: '📥' },
      { threshold: 30, label: 'Converting Audio', icon: '🔄' },
      { threshold: 50, label: 'Validating File', icon: '✓' },
      { threshold: 60, label: 'AI Processing', icon: '🧠' },
      { threshold: 90, label: 'Generating MIDI', icon: '🎵' },
      { threshold: 100, label: 'Complete', icon: '🎉' }
    ];

    return steps.map((step, index) => ({
      ...step,
      active: progress >= step.threshold,
      current: index < steps.length - 1 && progress >= step.threshold && progress < steps[index + 1].threshold
    }));
  };

  return (
    <div className="progress-container">
      <div className="progress-header">
        <h3>
          {getStatusIcon()} Processing Audio
        </h3>
        <button
          type="button"
          className="btn btn-secondary cancel-btn"
          onClick={onReset}
          disabled={status === 'completed'}
        >
          Cancel
        </button>
      </div>

      <div className="progress-main">
        <div className="progress-bar-container">
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ 
                width: `${progress}%`, 
                backgroundColor: getProgressColor() 
              }}
            />
          </div>
          <div className="progress-percentage">
            {progress}%
          </div>
        </div>

        <div className="progress-message">
          <p className={error ? 'error' : ''}>{error || message}</p>
        </div>

        {!error && (
          <div className="progress-steps">
            {getProgressSteps().map((step, index) => (
              <div
                key={index}
                className={`progress-step ${step.active ? 'active' : ''} ${step.current ? 'current' : ''}`}
              >
                <div className="step-icon">{step.icon}</div>
                <div className="step-label">{step.label}</div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="error-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={onReset}
            >
              Try Again
            </button>
          </div>
        )}
      </div>

      <div className="progress-info">
        <p><strong>Process ID:</strong> {processId}</p>
        <p>This process typically takes 30 seconds to 2 minutes depending on file size and complexity.</p>
      </div>
    </div>
  );
};

export default ProgressBar;