"""
Configuration management for VigilancePilot.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv


# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Main configuration class for VigilancePilot."""
    
    # LLM Configuration
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4-turbo-preview"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    
    # Postman Configuration
    postman_api_key: Optional[str] = field(default_factory=lambda: os.getenv("POSTMAN_API_KEY"))
    postman_workspace_id: Optional[str] = field(default_factory=lambda: os.getenv("POSTMAN_WORKSPACE_ID"))
    
    # Redis Configuration
    redis_host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    redis_password: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))
    redis_db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    
    # RedisVL Configuration
    redisvl_index_name: str = field(default_factory=lambda: os.getenv("REDISVL_INDEX_NAME", "vigilancepilot_vectors"))
    redisvl_vector_dim: int = field(default_factory=lambda: int(os.getenv("REDISVL_VECTOR_DIM", "1536")))
    
    # Telnyx Configuration (Optional)
    telnyx_api_key: Optional[str] = field(default_factory=lambda: os.getenv("TELNYX_API_KEY"))
    telnyx_from_number: Optional[str] = field(default_factory=lambda: os.getenv("TELNYX_FROM_NUMBER"))
    telnyx_to_number: Optional[str] = field(default_factory=lambda: os.getenv("TELNYX_TO_NUMBER"))
    
    # Luma Configuration (Optional)
    luma_api_key: Optional[str] = field(default_factory=lambda: os.getenv("LUMA_API_KEY"))
    
    # Application Settings
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    confidence_threshold: float = field(default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD", "0.75")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    
    def validate(self) -> None:
        """Validate required configuration."""
        errors = []
        
        if self.llm_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI provider")
        
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")
        
        if not self.postman_api_key:
            errors.append("POSTMAN_API_KEY is required")
        
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables and optional config file.
    
    Args:
        config_path: Optional path to YAML config file
        
    Returns:
        Config object
    """
    config = Config()
    
    if config_path:
        import yaml
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
            # Override with file config if provided
            for key, value in config_data.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        attr_name = f"{key}_{subkey}"
                        if hasattr(config, attr_name):
                            setattr(config, attr_name, subvalue)
                elif hasattr(config, key):
                    setattr(config, key, value)
    
    config.validate()
    return config
