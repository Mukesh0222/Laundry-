from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_DATABASE: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()


print("\n[DEBUG] Loaded .env values:")
print("MYSQL_USER:", settings.MYSQL_USER)
print("MYSQL_PASSWORD:", settings.MYSQL_PASSWORD)  
print("MYSQL_HOST:", settings.MYSQL_HOST)
print("MYSQL_PORT:", settings.MYSQL_PORT)
print("MYSQL_DATABASE:", settings.MYSQL_DATABASE)
