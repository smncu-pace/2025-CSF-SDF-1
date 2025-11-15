"""
API测试
"""

import pytest
import json
import os
import tempfile
from app import create_app
from config import Config

class TestConfig(Config):
    TESTING = True
    UPLOAD_FOLDER = tempfile.mkdtemp()

@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_hello_endpoint(client):
    """测试欢迎接口"""
    response = client.get('/api/hello')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'timestamp' in data

def test_calculate_endpoint(client):
    """测试计算接口"""
    response = client.post('/api/calculate', 
                         json={'expression': '2+3*4'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['result'] == 14

def test_invalid_calculation(client):
    """测试无效计算"""
    response = client.post('/api/calculate', 
                         json={'expression': '2+'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data