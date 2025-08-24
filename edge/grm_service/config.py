"""
Configuration management for GRM Service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Edge Core Configuration
    IZUMA_API_BASE_URL: str = Field(
        default="ws://192.168.1.198:8081",
        description="Edge Core WebSocket URL"
    )
    IZUMA_DEVICE_ID: Optional[str] = Field(
        default=None,
        description="Device ID for GRM registration"
    )
    
    # Service Configuration
    SERVICE_NAME: str = Field(
        default="edge-grm-service",
        description="Service name for registration"
    )
    SERVICE_VERSION: str = Field(
        default="1.0.0",
        description="Service version"
    )
    
    # Resource Configuration
    RESOURCES_FILE: str = Field(
        default="resources.json",
        description="Path to resources configuration file"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="Log format string"
    )
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = Field(
        default=30,
        description="Health check interval in seconds"
    )
    
    # Resource Update Configuration
    RESOURCE_UPDATE_INTERVAL: int = Field(
        default=60,
        description="Resource update interval in seconds"
    )
    
    # Retry Configuration
    MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retries for API calls"
    )
    RETRY_DELAY: int = Field(
        default=5,
        description="Delay between retries in seconds"
    )
    
    class Config:
        env_file = [".env", "test.env"]
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
