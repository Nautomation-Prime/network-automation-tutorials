from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AutomationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NETAUTO_", env_file=".env")

    username: str
    password: SecretStr
    vault_url: str = "https://vault.example.internal"
    max_workers: int = 10


settings = AutomationSettings()   # reads NETAUTO_USERNAME, NETAUTO_PASSWORD, ...

print(settings.password)                    # **********  — safe to log
print(settings.password.get_secret_value()) # the real value, only where needed
