"""
Python HTTP后端服务器
为Qt前端提供RESTful API服务
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from config import Config

# 导入路由
from routes.api_routes import api_bp
from routes.file_routes import file_bp

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 启用CORS，允许所有域名访问（在生产环境中应该限制）
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册蓝图
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(file_bp, url_prefix='/api')
    
    # 创建上传目录
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 根路由 - 提供服务器信息
    @app.route('/')
    def index():
        return jsonify({
            "message": "Python HTTP后端服务器",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "GET /api/": "API信息",
                "GET /api/hello": "欢迎消息",
                "GET|POST /api/messages": "消息管理",
                "POST /api/calculate": "数学计算",
                "GET /api/status": "服务器状态",
                "POST /api/upload": "文件上传",
                "GET /api/files": "文件列表",
                "GET /api/download/<filename>": "文件下载"
            }
        })
    
    # 健康检查端点
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "端点不存在", "code": 404}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "服务器内部错误", "code": 500}), 500
    
    # 日志配置
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    return app

def get_local_ip():
    """获取本机IP地址"""
    import socket
    try:
        # 连接一个外部地址但不发送数据
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    app = create_app()
    
    local_ip = get_local_ip()
    port = app.config.get('PORT', 6612)
    
    print("=" * 60)
    print("Python HTTP后端服务器启动信息")
    print("=" * 60)
    print(f"本地访问: http://127.0.0.1:{port}")
    print(f"局域网访问: http://{local_ip}:{port}")
    print(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    print(f"调试模式: {app.debug}")
    print("=" * 60)
    print("在Qt客户端中使用上述局域网地址进行连接")
    print("=" * 60)
    
    # 启动服务器
    app.run(
        host='0.0.0.0',  # 监听所有网络接口
        port=port,
        debug=app.config.get('DEBUG', True),
        threaded=True  # 支持并发请求
    )
