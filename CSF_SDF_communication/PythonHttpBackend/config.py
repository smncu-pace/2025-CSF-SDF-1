import os
from datetime import timedelta

class Config:
    """应用配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    PORT = int(os.environ.get('PORT', 6612))
    
    # 文件上传配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 最大文件大小
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 
        'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'
    }
    
    # CORS配置
    CORS_ORIGINS = ['*']  # 生产环境中应该限制为具体域名
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # API配置
    API_PREFIX = '/api'
    MESSAGES_LIMIT = 100  # 最大消息保存数量