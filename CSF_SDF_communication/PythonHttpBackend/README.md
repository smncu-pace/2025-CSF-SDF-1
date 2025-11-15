# Python HTTP后端服务器

为Qt前端应用提供RESTful API服务的Python后端。

## 功能特性

- ✅ RESTful API设计
- ✅ 文件上传和下载
- ✅ 数学计算服务
- ✅ 消息管理系统
- ✅ 跨域请求支持 (CORS)
- ✅ 完整的错误处理
- ✅ 系统状态监控
- ✅ 自动局域网IP检测

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行服务器

```bash
python app.py
```

### 3. 访问服务器

服务器启动后会显示访问地址：
- 本地访问: `http://127.0.0.1:5000`
- 局域网访问: `http://192.168.x.x:5000`

## API文档

### 基础端点

- `GET /` - 服务器信息
- `GET /health` - 健康检查

### API端点

- `GET /api/hello` - 欢迎消息
- `GET/POST /api/messages` - 消息管理
- `POST /api/calculate` - 数学计算
- `GET /api/status` - 服务器状态
- `POST /api/upload` - 文件上传
- `GET /api/files` - 文件列表
- `GET /api/download/<filename>` - 文件下载

## 配置

修改 `config.py` 文件或设置环境变量：

- `PORT` - 服务器端口 (默认: 5000)
- `DEBUG` - 调试模式 (默认: True)
- `UPLOAD_FOLDER` - 上传文件目录 (默认: uploads)

## 测试

```bash
pytest tests/
```

## 与Qt前端配合

在Qt客户端中设置服务器地址为显示的局域网地址，例如：
`http://192.168.1.100:5000`
```

## 运行说明

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行服务器

```bash
python app.py
```

### 3. 测试API

服务器启动后，你可以通过以下方式测试：

```bash
# 测试欢迎接口
curl "http://localhost:5000/api/hello?name=TestUser"

# 测试计算接口
curl -X POST "http://localhost:5000/api/calculate" \
     -H "Content-Type: application/json" \
     -d '{"expression": "2+3*4"}'

# 测试文件上传
curl -X POST "http://localhost:5000/api/upload" \
     -F "file=@/path/to/your/file.txt"
```

### 4. 配置Qt客户端

在Qt客户端中，将服务器地址设置为：
```
http://你的IP地址:5000
```

## 功能特点

1. **完整的RESTful API** - 符合REST设计原则
2. **安全文件处理** - 安全的文件名处理和类型检查
3. **数学表达式安全评估** - 防止代码注入攻击
4. **跨域支持** - 允许前端应用跨域访问
5. **错误处理** - 完善的错误处理和状态码返回
6. **系统监控** - 服务器状态和资源使用监控
7. **自动IP检测** - 自动检测局域网IP便于连接

这个完整的Python后端与前面的Qt前端完美配合，提供了完整的HTTP通信解决方案。