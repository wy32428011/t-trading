from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str = "172.16.3.64"
    db_port: int = 49030
    db_name: str = "stock"
    db_user: str = "root"
    db_password: str = ""

    llm_base_url: str = "http://172.16.3.64:49090/v1"
    llm_model: str = "Qwen3-235B-A22B-Instruct-2507"
    llm_api_key: str = "test_qwen"
    class Config:
        env_file = ".env"


settings = Settings()