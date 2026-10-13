import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    app_name: str = "AI Resume & Job Description Matcher"
    version: str = "1.0.0"
    debug: bool = False
    
    # Server & Network
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000"
    ]
    
    # File Upload Restrictions
    max_upload_size_mb: int = 5
    allowed_extensions: List[str] = [".pdf", ".docx"]
    min_extracted_text_chars: int = 50
    
    # Embedding Model
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Scoring System Weights
    semantic_weight: float = 0.40
    required_skill_weight: float = 0.40
    preferred_skill_weight: float = 0.20
    
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
