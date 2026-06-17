import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# 1. Load Secrets from .env
class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# 2. Define the YAML Structure
class RateLimitConfig(BaseModel):
    requests_per_minute: int
    tokens_per_minute: int

class TeamConfig(BaseModel):
    team_id: str
    allowed_models: list[str]
    daily_budget_usd: float
    rate_limits: RateLimitConfig

class GatewayConfig(BaseModel):
    teams: list[TeamConfig]

# 3. Loader Function
def load_yaml_config(path: str = "config/config.yaml") -> GatewayConfig:
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return GatewayConfig(**data)
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file not found at {path}")

# 4. Instantiate globally so other files can import them
settings = Settings()
gateway_config = load_yaml_config()