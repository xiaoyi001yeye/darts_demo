#!/bin/bash

echo "🚀 开始API接口测试..."
echo "====================================="

# 清理之前的容器
echo "清理之前的测试容器..."
docker-compose -f docker-compose.test.yml down --remove-orphans

# 构建并启动测试环境
echo "构建并启动测试环境..."
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# 获取测试结果
echo "====================================="
echo "🔍 测试完成，检查结果..."

# 显示容器日志
echo "📋 后端服务日志:"
docker logs darts_backend_test

echo ""
echo "📋 API测试日志:"
docker logs darts_api_tester

# 清理测试环境
echo ""
echo "🧹 清理测试环境..."
docker-compose -f docker-compose.test.yml down --remove-orphans

echo "✅ 测试流程完成!"