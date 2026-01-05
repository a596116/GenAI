"""
配置管理模組
使用 Pydantic Settings 管理環境變數
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """應用程式設定"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    
    # MySQL Database Configuration
    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_user: str = Field(..., alias="MYSQL_USER")
    mysql_password: str = Field(..., alias="MYSQL_PASSWORD")
    mysql_database: str = Field(..., alias="MYSQL_DATABASE")
    
    # Vanna Configuration
    vanna_model: str = Field(default="my_vanna_model", alias="VANNA_MODEL")
    
    # Application Settings
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def mysql_connection_string(self) -> str:
        """生成 MySQL 連接字串"""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    @property
    def mysql_config(self) -> dict:
        """返回 MySQL 配置字典"""
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database
        }


# 全局設定實例
settings = Settings()

