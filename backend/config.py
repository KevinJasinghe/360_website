"""
Production-safe configuration for Flask app
"""
import os
from pathlib import Path

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB default
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
    
    # AI Model settings
    WEIGHTS_FOLDER = os.environ.get('WEIGHTS_FOLDER', 'weights')
    MODEL_PATH = os.environ.get('MODEL_PATH', 'weights/piano_transcription_weights.pth')
    
    # Processing limits
    MAX_AUDIO_DURATION = int(os.environ.get('MAX_AUDIO_DURATION', 600))  # 10 minutes
    MAX_YOUTUBE_DURATION = int(os.environ.get('MAX_YOUTUBE_DURATION', 600))  # 10 minutes
    CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', 3600))  # 1 hour
    
    # Server settings
    PORT = int(os.environ.get('PORT', 3001))
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration"""
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Ensure weights directory exists
        os.makedirs(app.config['WEIGHTS_FOLDER'], exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    UPLOAD_FOLDER = '../uploads'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Use /tmp for uploads in production (ephemeral storage)
    UPLOAD_FOLDER = '/tmp/uploads'
    
    # Stricter limits for production
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    MAX_AUDIO_DURATION = 300  # 5 minutes
    MAX_YOUTUBE_DURATION = 300  # 5 minutes
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # Setup file logging
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/piano_transcription.log', 
                                             maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Piano Transcription startup')

class TestConfig(Config):
    """Testing configuration"""
    TESTING = True
    UPLOAD_FOLDER = '/tmp/test_uploads'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB for testing

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}