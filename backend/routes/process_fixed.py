    def _process_file_background(self, process_id):
        """Background processing function"""
        from flask import current_app
        
        # Create application context for background thread
        with current_app.app_context():
            try:
                from app import processing_status
                
                process_info = processing_status[process_id]
                process_type = process_info.get('type', 'upload')
                
                # Step 1: Handle YouTube download if needed
                if process_type == 'youtube':
                    self._update_progress(process_id, 10, "Downloading from YouTube...")
                    
                    url = process_info['url']
                    video_info = process_info['video_info']
                    
                    # Create download filename
                    safe_title = YouTubeDownloader.sanitize_filename(video_info['title'])
                    download_filename = f"{process_id}_{safe_title}.wav"
                    download_path = os.path.join(current_app.config['UPLOAD_FOLDER'], download_filename)
                    
                    # Download audio
                    success, message = YouTubeDownloader.download_audio(url, download_path)
                    if not success:
                        self._update_progress(process_id, 0, f"Download failed: {message}", status='failed')
                        return
                    
                    # Update process info with file path
                    processing_status[process_id]['file_path'] = download_path
                    processing_status[process_id]['original_filename'] = f"{video_info['title']}.wav"
                
                # Step 2: Get file path
                file_path = process_info.get('file_path')
                if not file_path or not os.path.exists(file_path):
                    self._update_progress(process_id, 0, "File not found", status='failed')
                    return
                
                # Step 3: Convert to WAV if needed
                self._update_progress(process_id, 30, "Converting to WAV format...")
                
                wav_filename = f"{process_id}_converted.wav"
                wav_path = os.path.join(current_app.config['UPLOAD_FOLDER'], wav_filename)
                
                # Check if already WAV
                original_filename = process_info.get('original_filename', '')
                if original_filename.lower().endswith('.wav'):
                    # Copy/rename the file
                    import shutil
                    shutil.copy2(file_path, wav_path)
                    conversion_success = True
                    conversion_message = "File already in WAV format"
                else:
                    # Convert to WAV
                    conversion_success, conversion_message = FileConverter.convert_to_wav(file_path, wav_path)
                
                if not conversion_success:
                    self._update_progress(process_id, 30, f"Conversion failed: {conversion_message}", status='failed')
                    return
                
                # Step 4: Validate WAV file
                self._update_progress(process_id, 50, "Validating audio file...")
                
                is_valid, validation_message = AIProcessor.validate_wav_file(wav_path)
                if not is_valid:
                    self._update_progress(process_id, 50, f"Validation failed: {validation_message}", status='failed')
                    return
                
                # Step 5: Process with AI model
                self._update_progress(process_id, 60, "Processing with AI model...")
                
                midi_filename = f"{process_id}_output.mid"
                midi_path = os.path.join(current_app.config['UPLOAD_FOLDER'], midi_filename)
                
                ai_success, ai_message = AIProcessor.process_audio_to_midi(wav_path, midi_path)
                if not ai_success:
                    self._update_progress(process_id, 60, f"AI processing failed: {ai_message}", status='failed')
                    return
                
                # Step 6: Complete processing
                self._update_progress(process_id, 100, "Processing completed successfully!", status='completed')
                
                # Store MIDI file info
                processing_status[process_id]['midi_path'] = midi_path
                processing_status[process_id]['midi_filename'] = midi_filename
                processing_status[process_id]['midi_ready'] = True
                
                # Clean up intermediate files
                try:
                    if wav_path != file_path and os.path.exists(wav_path):
                        os.remove(wav_path)
                    if process_type == 'youtube' and file_path != wav_path and os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass  # Don't fail if cleanup fails
                    
            except Exception as e:
                self._update_progress(process_id, 0, f"Processing error: {str(e)}", status='failed')