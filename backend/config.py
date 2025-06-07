import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Existing API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # New Agentic Cloner API Keys
    browserbase_api_key: str = os.getenv("BROWSERBASE_API_KEY", "")
    browserbase_project_id: str = os.getenv("BROWSERBASE_PROJECT_ID", "")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    zep_api_key: str = os.getenv("ZEP_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Application Settings
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    max_clone_time: int = 120
    max_concurrent_clones: int = 5
    
    # Browser Settings
    headless_browser: bool = True
    browser_timeout: int = 120000
    
    # Storage
    assets_storage_path: str = "./storage/assets"
    screenshots_path: str = "./storage/screenshots"
    
    # New Agentic Cloner Settings
    max_tokens: int = 8000
    cost_limit_usd: float = 0.10
    timeout_seconds: int = 25
    supabase_bucket_name: str = "rawsites"
    target_image_width: int = 400
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()

# Create storage directories if they don't exist
os.makedirs(settings.assets_storage_path, exist_ok=True)
os.makedirs(settings.screenshots_path, exist_ok=True) 