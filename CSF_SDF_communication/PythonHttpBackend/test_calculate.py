#!/usr/bin/env python3
"""
测试计算接口的脚本
"""

import requests
import json
import sys

def test_calculate(server_url):
    """测试计算接口"""

    print(f"测试服务器: {server_url}")
    print("=" * 50)

    # 测试GET请求
    print("1. 测试GET请求:")
    try:
        response = requests.get(f"{server_url}/api/calculate?expression=2%2B3*4")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   错误: {e}")

    print("\n2. 测试POST请求:")
    try:
        data = {"expression": "2+3*4"}
        response = requests.post(
            f"{server_url}/api/calculate",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   错误: {e}")

    print("\n3. 测试错误表达式:")
    try:
        data = {"expression": "2+"}
        response = requests.post(
            f"{server_url}/api/calculate",
            json=data
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   错误: {e}")

if __name__ == "__main__":
    server_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]

    test_calculate(server_url)