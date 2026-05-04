from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    kxaio_api_key: str
    database_url: str = "sqlite:///./kxaio_events.db"

    stripe_webhook_secret: str = ""
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_webhook_id: str = ""
    paypal_env: str = "sandbox"

    woocommerce_webhook_secret: str = ""
    n8n_shared_secret: str = ""

    openai_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

print("KXAIO KEY LOADED:", settings.kxaio_api_key)