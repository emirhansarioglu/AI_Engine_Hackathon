"""Configuration settings for Runware + Mirelo AI Web Application"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # ============================================
    # API Configuration
    # ============================================
    RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")    
    # ============================================
    # Directory Structure (Cloud-friendly)
    # ============================================
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Static files
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")  # Temporary uploaded images
    
    # Output files (these should be in cloud storage in production)
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "output"))
    VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")  # Videos without audio
    TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")  # Temporary processing files
    
    # ============================================
    # Web Application Settings
    # ============================================
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Upload limits
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB default
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    
    # Session timeout
    UPLOAD_SESSION_TIMEOUT = int(os.getenv("UPLOAD_SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # ============================================
    # Runware Settings
    # ============================================
    DEFAULT_DURATION = int(os.getenv("DEFAULT_DURATION", "5"))
    DEFAULT_RATIO = os.getenv("DEFAULT_RATIO", "16:9")
    DEFAULT_PROMPT = os.getenv("DEFAULT_PROMPT", "")
    
    # Video ratio options
    RATIO_OPTIONS = ["16:9", "9:16", "1:1", "4:3", "3:4"]
    
    # ============================================
    # Pipeline Settings
    # ============================================
    # Whether to keep intermediate files
    KEEP_INTERMEDIATE_FILES = os.getenv("KEEP_INTERMEDIATE_FILES", "true").lower() == "true"
    
    # Auto-download videos after generation
    AUTO_DOWNLOAD_VIDEOS = os.getenv("AUTO_DOWNLOAD_VIDEOS", "true").lower() == "true"
    
    # Maximum concurrent operations
    MAX_CONCURRENT_OPERATIONS = int(os.getenv("MAX_CONCURRENT_OPERATIONS", "5"))
    
    # Retry settings
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))  # seconds
    
    # Job cleanup - delete jobs older than X days
    JOB_RETENTION_DAYS = int(os.getenv("JOB_RETENTION_DAYS", "7"))
    
    # ============================================
    # Logging Settings
    # ============================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.path.join(OUTPUT_DIR, "pipeline.log")
    
    # ============================================
    # Pipeline State Management
    # ============================================
    STATE_FILE = os.path.join(OUTPUT_DIR, "pipeline_state.json")
    
    @classmethod
    def validate(cls):
        """Validate required configuration and create necessary directories"""
        errors = []
        
        # Check Runware API key
        if not cls.RUNWARE_API_KEY:
            errors.append("RUNWARE_API_KEY not set in environment variables")
        
        if errors:
            raise ValueError("\n".join(errors))
        
        # Create all necessary directories
        directories = [
            cls.STATIC_DIR,
            cls.UPLOADS_DIR,
            cls.OUTPUT_DIR,
            cls.VIDEOS_DIR,
            cls.TEMP_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        print("✓ Configuration validated")
        print(f"  - Static directory: {cls.STATIC_DIR}")
        print(f"  - Uploads directory: {cls.UPLOADS_DIR}")
        print(f"  - Videos output: {cls.VIDEOS_DIR}")
        
        return True
    
    @classmethod
    def get_pipeline_stage_dir(cls, stage: str) -> str:
        """
        Get output directory for specific pipeline stage
        
        Args:
            stage: Pipeline stage name ('runware', 'mirelo', 'temp')
        
        Returns:
            str: Directory path for the stage
        """
        stage_map = {
            'runware': cls.VIDEOS_DIR,
            'temp': cls.TEMP_DIR,
            'uploads': cls.UPLOADS_DIR
        }
        
        return stage_map.get(stage.lower(), cls.OUTPUT_DIR)