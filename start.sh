#!/bin/bash

echo "=========================================="
echo "🚀 启动 Darts 时间序列预测系统"
echo "=========================================="

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查 docker-compose 是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose 未安装，请先安装 docker-compose"
    exit 1
fi

echo "📦 构建并启动服务..."

# 构建并启动服务
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

echo ""
echo "=========================================="
echo "✅ 系统启动完成！"
echo "=========================================="
echo "🌐 前端访问地址: http://localhost"
echo "🔗 后端 API 地址: http://localhost:5001"
echo "📊 健康检查: http://localhost:5001/api/health"
echo ""
echo "🛠️  管理命令:"
echo "   停止服务: docker-compose down"
echo "   查看日志: docker-compose logs -f"
echo "   重启服务: docker-compose restart"
echo "=========================================="