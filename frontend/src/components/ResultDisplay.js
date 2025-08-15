import React, { useState } from 'react';
import axios from 'axios';
import './ResultDisplay.css';

const ResultDisplay = ({ result, processId, onReset }) => {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState('');
  const [sheetMusicDownloading, setSheetMusicDownloading] = useState(false);
  const [sheetMusicError, setSheetMusicError] = useState('');

  const handleDownload = async () => {
    if (!result.midiReady) {
      setDownloadError('MIDI file is not ready for download');
      return;
    }

    setDownloading(true);
    setDownloadError('');

    try {
      const response = await axios.get(`/api/download/${processId}`, {
        responseType: 'blob',
      });

      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      // Extract filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'sheet_music.mid';
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      link.remove();
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Download error:', error);
      if (error.response?.data?.error) {
        setDownloadError(error.response.data.error);
      } else {
        setDownloadError('Download failed: ' + error.message);
      }
    } finally {
      setDownloading(false);
    }
  };

  const handleSheetMusicDownload = async (format = 'musicxml') => {
    if (!result.midiReady) {
      setSheetMusicError('MIDI file is not ready for sheet music conversion');
      return;
    }

    setSheetMusicDownloading(true);
    setSheetMusicError('');

    try {
      // First, generate the sheet music
      const generateResponse = await axios.post(`/api/sheet-music/${processId}`, {
        format: format
      });

      if (generateResponse.data.success) {
        // Then download it
        const downloadResponse = await axios.get(`/api/sheet-music/download/${processId}?format=${format}`, {
          responseType: 'blob',
        });

        // Create blob link to download
        const url = window.URL.createObjectURL(new Blob([downloadResponse.data]));
        const link = document.createElement('a');
        link.href = url;

        // Set filename based on format
        const filename = format === 'musicxml' 
          ? `sheet_music_${processId.slice(0, 8)}.xml`
          : `sheet_music_${processId.slice(0, 8)}.png`;

        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        
        // Clean up
        link.remove();
        window.URL.revokeObjectURL(url);
      } else {
        setSheetMusicError('Failed to generate sheet music: ' + generateResponse.data.message);
      }

    } catch (error) {
      console.error('Sheet music download error:', error);
      if (error.response?.data?.error) {
        setSheetMusicError(error.response.data.error);
      } else {
        setSheetMusicError('Sheet music download failed: ' + error.message);
      }
    } finally {
      setSheetMusicDownloading(false);
    }
  };

  const formatProcessId = (id) => {
    return id.slice(0, 8) + '...';
  };

  return (
    <div className="result-container">
      <div className="result-header">
        <div className="success-icon">🎉</div>
        <h3>Conversion Complete!</h3>
        <p>Your audio has been successfully converted to MIDI sheet music</p>
      </div>

      <div className="result-content">
        <div className="result-info">
          <div className="info-card">
            <div className="info-icon">📄</div>
            <div className="info-details">
              <h4>MIDI File Generated</h4>
              <p>Your sheet music is ready in MIDI format</p>
              <p className="process-id">Process ID: {formatProcessId(processId)}</p>
            </div>
          </div>

          <div className="result-actions">
            <button
              type="button"
              className="btn btn-success download-btn"
              onClick={handleDownload}
              disabled={downloading || !result.midiReady}
            >
              {downloading ? (
                <>
                  <span className="loading-spinner"></span>
                  Downloading...
                </>
              ) : (
                <>
                  📥 Download MIDI File
                </>
              )}
            </button>

            <button
              type="button"
              className="btn btn-primary download-btn"
              onClick={() => handleSheetMusicDownload('musicxml')}
              disabled={sheetMusicDownloading || !result.midiReady}
              style={{ marginLeft: '10px' }}
            >
              {sheetMusicDownloading ? (
                <>
                  <span className="loading-spinner"></span>
                  Generating...
                </>
              ) : (
                <>
                  🎼 Download Sheet Music (XML)
                </>
              )}
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={onReset}
              style={{ marginLeft: '10px' }}
            >
              🔄 Convert Another File
            </button>
          </div>

          {downloadError && (
            <div className="error-message">
              <span>❌ {downloadError}</span>
            </div>
          )}

          {sheetMusicError && (
            <div className="error-message">
              <span>❌ Sheet Music: {sheetMusicError}</span>
            </div>
          )}
        </div>

        <div className="midi-info">
          <h4>📋 About Your MIDI File</h4>
          <ul>
            <li><strong>Format:</strong> Standard MIDI (.mid)</li>
            <li><strong>Compatibility:</strong> Works with most music software</li>
            <li><strong>Usage:</strong> Import into DAWs, notation software, or MIDI players</li>
            <li><strong>Editing:</strong> Can be edited in programs like MuseScore, Sibelius, or Logic Pro</li>
          </ul>
        </div>

        <div className="software-suggestions">
          <h4>🎼 Recommended Software</h4>
          <div className="software-grid">
            <div className="software-item">
              <div className="software-icon">🎵</div>
              <div className="software-info">
                <h5>MuseScore</h5>
                <p>Free music notation software</p>
              </div>
            </div>
            <div className="software-item">
              <div className="software-icon">🎹</div>
              <div className="software-info">
                <h5>Piano Roll Editors</h5>
                <p>FL Studio, Logic Pro, Cubase</p>
              </div>
            </div>
            <div className="software-item">
              <div className="software-icon">📝</div>
              <div className="software-info">
                <h5>Notation Software</h5>
                <p>Sibelius, Finale, Dorico</p>
              </div>
            </div>
            <div className="software-item">
              <div className="software-icon">▶️</div>
              <div className="software-info">
                <h5>MIDI Players</h5>
                <p>VLC, Windows Media Player</p>
              </div>
            </div>
          </div>
        </div>

        <div className="usage-tips">
          <h4>💡 Tips for Best Results</h4>
          <ul>
            <li>The AI model works best with clear, isolated instrumental music</li>
            <li>Complex polyphonic music may require manual editing</li>
            <li>Use the MIDI file as a starting point for your sheet music</li>
            <li>Consider adjusting tempo and dynamics in your chosen software</li>
            <li>Multiple instruments may be mapped to different MIDI channels</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ResultDisplay;