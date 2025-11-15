"""
工具函数
"""

import os
import math
import re

def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_size(filepath):
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def safe_eval_expression(expression):
    """
    安全评估数学表达式
    只允许基本的数学运算和常用函数
    """
    
    # 移除空格
    expression = expression.replace(' ', '')
    
    # 允许的字符和模式
    allowed_chars = set('0123456789+-*/(). ')
    allowed_pattern = r'^[0-9+\-*/().\s]+$'
    
    # 检查字符
    if not all(c in allowed_chars for c in expression):
        raise ValueError("表达式包含不允许的字符")
    
    # 检查模式
    if not re.match(allowed_pattern, expression):
        raise ValueError("表达式格式不正确")
    
    # 检查括号匹配
    stack = []
    for char in expression:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                raise ValueError("括号不匹配")
            stack.pop()
    
    if stack:
        raise ValueError("括号不匹配")
    
    # 安全评估
    try:
        # 限制内置函数和变量
        safe_dict = {
            '__builtins__': {},
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
        }
        
        result = eval(expression, safe_dict)
        
        # 检查结果是否为数字
        if not isinstance(result, (int, float)):
            raise ValueError("计算结果不是数字")
        
        return result
    
    except ZeroDivisionError:
        raise ValueError("除以零错误")
    except:
        raise ValueError("无法计算表达式")

def validate_ip_address(ip):
    """简单的IP地址验证"""
    import socket
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False