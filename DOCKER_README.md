# 🚀 Docker 部署指南

这个项目已经配置好了 Docker 环境，可以一键启动整个时间序列预测系统。

## 📋 系统要求

- Docker (>= 20.0)
- Docker Compose (>= 2.0)
- 至少 2GB 可用内存

## 🏃‍♂️ 快速启动

### 方法 1: 使用启动脚本（推荐）

```bash
# 一键启动
./start.sh
```

### 方法 2: 手动启动

```bash
# 构建并启动所有服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 🌐 访问地址

启动成功后，你可以通过以下地址访问系统：

- **前端界面**: http://localhost
- **后端 API**: http://localhost:5001
- **健康检查**: http://localhost:5001/api/health

## 🛠️ 管理命令

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 重启服务
docker-compose restart

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 进入容器调试
docker-compose exec backend bash
docker-compose exec frontend sh
```

## 📁 项目结构

```
darts_demo/
├── docker-compose.yml      # Docker Compose 配置
├── start.sh               # 快速启动脚本
├── data/                  # 数据持久化目录
├── backend/               # 后端服务
│   ├── Dockerfile         # 后端 Docker 配置
│   ├── app.py            # Flask 应用
│   ├── requirements.txt   # Python 依赖
│   └── utils.py          # 工具函数
└── frontend/              # 前端服务
    ├── Dockerfile         # 前端 Docker 配置
    ├── nginx.conf        # Nginx 配置
    ├── index.html        # 主页面
    ├── css/              # 样式文件
    └── js/               # JavaScript 文件
```

## 🐛 故障排除

### 端口被占用

如果遇到端口被占用的问题，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 改为其他端口
  backend:
    ports:
      - "5002:5001"  # 改为其他端口
```

### 服务启动失败

检查 Docker 日志：

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend
```

### 清理和重建

如果需要完全重建：

```bash
# 停止并删除所有容器、网络和镜像
docker-compose down --rmi all -v

# 重新构建并启动
docker-compose up --build -d
```

## 🔧 开发模式

如果需要在开发模式下运行（代码修改后自动重载）：

```bash
# 修改 docker-compose.yml，添加卷挂载
volumes:
  - ./backend:/app
  - ./frontend:/usr/share/nginx/html

# 设置开发环境变量
environment:
  - FLASK_ENV=development
  - FLASK_DEBUG=1
```

## 📊 性能优化

### 生产环境配置

1. **调整内存限制**：
```yaml
services:
  backend:
    mem_limit: 1g
    cpus: 0.5
```

2. **使用预构建镜像**：
```bash
# 构建并推送到镜像仓库
docker build -t your-registry/darts-backend ./backend
docker build -t your-registry/darts-frontend ./frontend
```

3. **启用日志轮转**：
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔒 安全建议

1. 不要在生产环境中暴露调试端口
2. 使用环境变量管理敏感配置
3. 定期更新基础镜像
4. 配置防火墙规则限制访问

## 📝 更新说明

当代码有更新时：

```bash
# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up --build -d
```