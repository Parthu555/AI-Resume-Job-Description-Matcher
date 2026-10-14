import os
import json
from typing import List, Any, Union
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, field_validator

class Settings(BaseSettings):
    app_name: str = "AI Resume & Job Description Matcher"
    version: str = "1.0.0"
    debug: bool = False
    
    # Server & Network
    host: str = "127.0.0.1"
    port: int = 8000
    backend_url: str = "http://127.0.0.1:8000"
    frontend_port: int = 8501
    cors_origins: Union[List[str], str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000"
    ]
    
    # File Upload Restrictions
    max_upload_size_mb: int = 5
    allowed_extensions: Union[List[str], str] = [".pdf", ".docx"]
    min_extracted_text_chars: int = 50
    
    # Embedding Model
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Scoring System Weights
    semantic_weight: float = 0.40
    required_skill_weight: float = 0.40
    preferred_skill_weight: float = 0.20
    
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("allowed_extensions")
    @classmethod
    def parse_allowed_extensions(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

settings = Settings()

