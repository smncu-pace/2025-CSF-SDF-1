from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入模型（让 Flask-Migrate 知道这些表存在）
from .models import User, Memory, Picture, Comment, Message
