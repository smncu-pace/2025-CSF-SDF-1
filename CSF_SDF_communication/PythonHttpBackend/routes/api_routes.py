"""
API路由定义
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import math
import re
import sys

from models import data_store
from utils.helpers import safe_eval_expression

# 创建API蓝图
api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def api_info():
    """API信息端点"""
    return jsonify({
        "name": "Python后端API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "/hello": "GET - 欢迎消息",
            "/messages": "GET/POST - 消息管理", 
            "/calculate": "POST - 数学计算",
            "/status": "GET - 服务器状态"
        }
    })

@api_bp.route('/hello', methods=['GET'])
def hello():
    """欢迎接口"""
    name = request.args.get('name', '匿名用户')
    
    return jsonify({
        "message": f"你好, {name}!",
        "timestamp": datetime.now().isoformat(),
        "server": "Python Flask服务器",
        "client_ip": request.remote_addr
    })

@api_bp.route('/messages', methods=['GET', 'POST'])
def handle_messages():
    """消息处理接口"""
    
    if request.method == 'GET':
        # 获取消息列表
        limit = request.args.get('limit', 50, type=int)
        messages = data_store.get_messages(limit)
        
        return jsonify({
            "count": len(messages),
            "limit": limit,
            "messages": messages,
            "timestamp": datetime.now().isoformat()
        })
    
    elif request.method == 'POST':
        # 创建新消息
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "请求体必须是JSON格式"}), 400
        
        if 'content' not in data or not data['content'].strip():
            return jsonify({"error": "消息内容不能为空"}), 400
        
        content = data['content'].strip()
        author = data.get('author', '匿名').strip() or '匿名'
        
        # 添加消息到存储
        message = data_store.add_message(
            content=content,
            author=author,
            ip=request.remote_addr
        )
        
        return jsonify({
            "status": "消息已接收",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }), 201
    

@api_bp.route('/calculate', methods=['GET', 'POST'])  # 同时支持GET和POST以便调试
def calculate():
    """数学计算接口"""
    # 记录请求信息用于调试
    current_app.logger.info(f"收到计算请求: 方法={request.method}, 远程地址={request.remote_addr}")

    if request.method == 'GET':
        # 对于GET请求，从查询参数获取表达式
        expression = request.args.get('expression', '')
        current_app.logger.info(f"GET请求表达式: {expression}")

        if not expression:
            return jsonify({
                "error": "缺少表达式参数",
                "usage": "使用GET请求时请提供expression查询参数，例如: /api/calculate?expression=2%2B3",
                "example": "http://localhost:5000/api/calculate?expression=2%2B3*4"
            }), 400
    else:
        # 对于POST请求，从JSON体获取数据
        if not request.is_json:
            return jsonify({
                "error": "请求必须是JSON格式",
                "content_type": request.content_type
            }), 400

        data = request.get_json()
        current_app.logger.info(f"POST请求数据: {data}")

        if not data:
            return jsonify({"error": "请求体必须是JSON格式"}), 400

        if 'expression' not in data:
            return jsonify({"error": "缺少表达式参数"}), 400

        expression = data['expression'].strip()

    if not expression:
        return jsonify({"error": "表达式不能为空"}), 400

    try:
        # 安全评估数学表达式
        result = safe_eval_expression(expression)

        # 记录计算历史
        data_store.add_message(
            content=f"计算: {expression} = {result}",
            author="系统",
            ip=request.remote_addr
        )

        response_data = {
            "expression": expression,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "calculated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method_used": request.method
        }

        current_app.logger.info(f"计算成功: {expression} = {result}")
        return jsonify(response_data)

    except ValueError as e:
        error_msg = f"计算错误: {str(e)}"
        current_app.logger.warning(f"{error_msg}, 表达式: {expression}")
        return jsonify({
            "error": error_msg,
            "expression": expression,
            "valid_examples": [
                "2 + 3 * 4",
                "(10 - 5) / 2",
                "3.14 * 2"
            ]
        }), 400
    except Exception as e:
        error_msg = f"服务器错误: {str(e)}"
        current_app.logger.error(f"{error_msg}, 表达式: {expression}")
        return jsonify({
            "error": error_msg,
            "expression": expression
        }), 500

@api_bp.route('/status', methods=['GET'])
def server_status():
    """服务器状态接口"""
    import psutil
    import os
    
    # 获取系统信息
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return jsonify({
        "status": "运行中",
        "server_time": datetime.now().isoformat(),
        "uptime_seconds": round(data_store.get_server_uptime(), 2),
        "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
        "messages_count": len(data_store.messages),
        "files_count": len(data_store.files),
        "client_ip": request.remote_addr,
        "system_info": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform
        }
    })