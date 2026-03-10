#!/bin/bash

# PostHog 监控系统部署脚本

set -e

echo "开始部署 PostHog 监控系统..."

# 1. 启动监控服务
echo "启动 Prometheus + Grafana + Exporters..."
docker-compose -f docker-compose.monitoring.yml up -d

# 2. 等待服务启动
echo "等待服务启动..."
sleep 15

# 3. 检查服务状态
echo ""
echo "检查服务状态:"
docker ps | grep -E "prometheus|grafana|cadvisor|kafka|clickhouse|node"

# 4. 配置 Grafana 数据源
echo ""
echo "配置 Grafana..."
sleep 5

curl -X POST http://admin:admin123@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Prometheus",
    "type":"prometheus",
    "url":"http://localhost:9090",
    "access":"proxy",
    "isDefault":true
  }' 2>/dev/null && echo "✓ Prometheus 数据源已添加" || echo "⚠ 数据源可能已存在"

echo ""
echo "=========================================="
echo "✓ 监控系统部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  Grafana:    http://$(hostname -I | awk '{print $1}'):3000"
echo "              用户名: admin"
echo "              密码: admin123"
echo ""
echo "  Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
echo ""
echo "监控内容："
echo "  ✓ Kafka 消费积压"
echo "  ✓ ClickHouse 状态"
echo "  ✓ Worker/Plugins 容器状态"
echo "  ✓ 系统 CPU/内存/磁盘"
echo "  ✓ 自动告警规则"
echo ""
echo "下一步："
echo "  1. 访问 Grafana"
echo "  2. 导入 Dashboard: dashboard.json"
echo "  3. 或导入社区 Dashboard: 893 (Docker) / 7589 (Kafka)"
echo ""
