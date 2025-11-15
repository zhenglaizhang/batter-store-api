#!/bin/bash

# 启动脚本
echo "启动 Battery Recycling API..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行，请先启动 Docker"
    exit 1
fi

# 启动服务
echo "使用 Docker Compose 启动服务..."
docker-compose up -d

# 等待 MySQL 就绪
echo "等待 MySQL 就绪..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo ""
echo "服务已启动！"
echo "API 地址: http://localhost:3000"
echo "查看日志: docker-compose logs -f app"
echo "停止服务: docker-compose down"

