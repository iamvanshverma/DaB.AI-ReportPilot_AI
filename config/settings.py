import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    RESEND_FROM_EMAIL = os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
    RESEND_FROM_NAME = os.getenv('RESEND_FROM_NAME', 'Mayank Paradkar')
    DEFAULT_RECIPIENT_EMAIL = os.getenv('DEFAULT_RECIPIENT_EMAIL', 'immayankparadkar@gmail.com')
    
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', './credentials.json')
    
    # Scheduler settings
    SCHEDULER_DB_PATH = "./scheduler_jobs.db"
    JOB_CONFIGS_DIR = "./job_configs"
    JOB_DATA_DIR = "./job_data"
    
    # Report settings
    MAX_ROWS_FOR_ANALYSIS = 5000
    MAX_CHARTS_IN_PDF = 6
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        errors = []
        
        if not cls.RESEND_API_KEY:
            errors.append("RESEND_API_KEY is missing")
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is missing")
        
        if not os.path.exists(cls.GOOGLE_SHEETS_CREDENTIALS_PATH):
            errors.append(f"Google Sheets credentials file not found at {cls.GOOGLE_SHEETS_CREDENTIALS_PATH}")
        
        return errors

settings = Settings()