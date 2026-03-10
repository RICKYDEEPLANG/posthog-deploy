#!/bin/bash

# PostHog 监控系统部署脚本

set -e

echo "开始部署 PostHog 监控系统..."

# 1. 启动监控服务
echo "启动 Prometheus + Grafana + Exporters..."
docker-compose -f docker-compose.monitoring.yml up -d

# 2. 等待服务启动
echo "等待服务启动..."
sleep 10

# 3. 检查服务状态
echo ""
echo "检查服务状态:"
docker ps | grep -E "prometheus|grafana|cadvisor|kafka-exporter"

echo ""
echo "=========================================="
echo "✓ 监控系统部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  Grafana:    http://localhost:3000"
echo "              用户名: admin"
echo "              密码: admin123"
echo ""
echo "  Prometheus: http://localhost:9090"
echo "  cAdvisor:   http://localhost:8082"
echo ""
echo "下一步："
echo "1. 访问 Grafana"
echo "2. 添加 Prometheus 数据源: http://localhost:9090"
echo "3. 导入 Dashboard ID: 893 (Docker 监控)"
echo "4. 导入 Dashboard ID: 7589 (Kafka 监控)"
echo ""
