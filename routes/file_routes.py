"""
文件上传下载路由
"""

import os
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from datetime import datetime

from models import data_store
from utils.helpers import allowed_file, get_file_size

# 创建文件蓝图
file_bp = Blueprint('file', __name__)

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """文件上传接口"""
    
    if 'file' not in request.files:
        return jsonify({"error": "没有选择文件"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    
    if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
        # 安全处理文件名
        filename = secure_filename(file.filename)
        
        # 生成唯一文件名避免冲突
        from time import time
        timestamp = int(time() * 1000)
        name, ext = os.path.splitext(filename)
        saved_filename = f"{timestamp}_{name}{ext}"
        
        # 保存文件
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)
        
        # 获取文件大小
        file_size = get_file_size(filepath)
        
        # 记录文件信息
        file_info = data_store.add_file(
            filename=filename,
            saved_name=saved_filename,
            size=file_size,
            ip=request.remote_addr
        )
        
        return jsonify({
            "status": "文件上传成功",
            "file": file_info,
            "download_url": f"/api/download/{saved_filename}",
            "timestamp": datetime.now().isoformat()
        }), 201
    
    else:
        allowed_extensions = ', '.join(current_app.config['ALLOWED_EXTENSIONS'])
        return jsonify({
            "error": f"文件类型不允许。允许的格式: {allowed_extensions}"
        }), 400

@file_bp.route('/files', methods=['GET'])
def list_files():
    """获取文件列表"""
    files = data_store.get_files()
    
    # 检查文件是否实际存在
    valid_files = []
    for file_info in files:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_info['saved_name'])
        if os.path.exists(filepath):
            valid_files.append(file_info)
        else:
            # 文件不存在，从记录中移除
            data_store.files.remove(file_info)
    
    return jsonify({
        "count": len(valid_files),
        "files": valid_files,
        "timestamp": datetime.now().isoformat()
    })

@file_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """文件下载接口"""
    
    # 安全检查文件名
    filename = secure_filename(filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({"error": "文件不存在"}), 404
    
    # 记录下载信息
    file_info = data_store.get_file_by_name(filename)
    if file_info:
        file_info['download_count'] = file_info.get('download_count', 0) + 1
        file_info['last_download'] = datetime.now().isoformat()
    
    # 发送文件
    return send_file(
        filepath,
        as_attachment=True,
        download_name=file_info['original_name'] if file_info else filename
    )

@file_bp.route('/file/<filename>', methods=['DELETE'])
def delete_file(filename):
    """删除文件接口"""
    
    filename = secure_filename(filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({"error": "文件不存在"}), 404
    
    try:
        # 删除文件
        os.remove(filepath)
        
        # 从记录中移除
        file_info = data_store.get_file_by_name(filename)
        if file_info:
            data_store.files.remove(file_info)
        
        return jsonify({
            "status": "文件删除成功",
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": f"删除文件失败: {str(e)}"}), 500