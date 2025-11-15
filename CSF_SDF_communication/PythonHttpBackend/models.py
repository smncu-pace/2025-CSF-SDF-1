"""
数据模型定义
"""

import time
from datetime import datetime
from typing import Dict, List, Any

class DataStore:
    """简单的内存数据存储"""
    
    def __init__(self):
        self.messages: List[Dict] = []
        self.files: List[Dict] = []
        self.server_start_time = time.time()
    
    def add_message(self, content: str, author: str = "匿名", ip: str = "unknown") -> Dict:
        """添加新消息"""
        message = {
            "id": len(self.messages) + 1,
            "content": content,
            "author": author,
            "timestamp": datetime.now().isoformat(),
            "ip": ip
        }
        self.messages.append(message)
        
        # 限制消息数量
        if len(self.messages) > 1000:
            self.messages = self.messages[-100:]
            
        return message
    
    def get_messages(self, limit: int = 50) -> List[Dict]:
        """获取消息列表"""
        return self.messages[-limit:] if self.messages else []
    
    def add_file(self, filename: str, saved_name: str, size: int, ip: str = "unknown") -> Dict:
        """添加文件记录"""
        file_info = {
            "id": len(self.files) + 1,
            "original_name": filename,
            "saved_name": saved_name,
            "size": size,
            "upload_time": datetime.now().isoformat(),
            "ip": ip
        }
        self.files.append(file_info)
        return file_info
    
    def get_files(self) -> List[Dict]:
        """获取文件列表"""
        return self.files
    
    def get_file_by_name(self, filename: str) -> Dict:
        """根据保存的文件名查找文件信息"""
        for file_info in self.files:
            if file_info['saved_name'] == filename:
                return file_info
        return None
    
    def get_server_uptime(self) -> float:
        """获取服务器运行时间（秒）"""
        return time.time() - self.server_start_time

# 全局数据存储实例
data_store = DataStore()