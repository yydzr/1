"""
配置文件
数据库连接配置、JWT 配置等
"""
import os
from datetime import timedelta


def _secret(name, dev_default):
    value = os.environ.get(name)
    if value:
        return value
    if os.environ.get('FLASK_ENV') == 'production':
        raise RuntimeError(f'{name} must be set in production')
    return dev_default


class Config:
    """应用配置"""
    # 数据库 — SQLite 文件数据库（数据随项目文件夹携带）
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'ai_efficiency.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设为 True 可查看 SQL 日志

    # JWT 配置：开发环境保留默认值，生产环境必须通过环境变量提供
    JWT_SECRET_KEY = _secret('JWT_SECRET_KEY', 'dev-only-jwt-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # DeepSeek AI 配置
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-your-deepseek-api-key')
    DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

    # 应用配置
    SECRET_KEY = _secret('SECRET_KEY', 'dev-only-flask-secret-change-me')
    JSON_AS_ASCII = False  # 支持中文 JSON 返回
    AUTO_CREATE_TABLES = os.environ.get('AUTO_CREATE_TABLES', 'true').lower() == 'true'
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            'CORS_ORIGINS',
            'http://localhost:3000,http://127.0.0.1:3000'
        ).split(',')
        if origin.strip()
    ]
