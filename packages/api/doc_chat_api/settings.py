from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API runtime configuration. Values come from environment variables.

    The api container reads these from the docker-compose `environment:` block,
    which is in turn populated by `make up` from CDK outputs.
    """

    database_url: str
    documents_bucket: str
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


def get_settings() -> Settings:
    return Settings()
