# PostHog 监控系统

## 包含内容

### 核心组件
- **Prometheus** - 时序数据库，数据采集
- **Grafana** - 可视化面板
- **cAdvisor** - 容器监控
- **Node Exporter** - 系统监控（CPU/内存/磁盘）
- **Kafka Exporter** - Kafka 监控
- **ClickHouse Exporter** - ClickHouse 监控

### 监控指标
- ✅ Kafka 消费积压量
- ✅ ClickHouse 运行状态和查询性能
- ✅ Worker 容器状态（内存、CPU、实例数）
- ✅ Plugins 容器状态（实例数、资源）
- ✅ Web 容器状态
- ✅ 系统资源（CPU、内存、磁盘）

### 告警规则
- Kafka 积压 > 50000 条
- ClickHouse 宕机
- Worker 容器宕机
- Plugins 实例 < 3
- 磁盘空间 < 10%
- 内存使用 > 90%

## 部署

### 1. 上传文件到服务器
```bash
# 上传这些文件到 /export/posthog/
- docker-compose.monitoring.yml
- prometheus.yml
- alerts.yml
- dashboard.json
- deploy-monitoring.sh
```

### 2. 执行部署
```bash
chmod +x deploy-monitoring.sh
./deploy-monitoring.sh
```

### 3. 访问 Grafana
```
地址: http://服务器IP:3000
用户名: admin
密码: admin123
```

### 4. 导入 Dashboard
方式 1：导入 dashboard.json（已包含 PostHog 专用面板）
方式 2：从社区导入
  - Dashboard ID: 893 (Docker 容器监控)
  - Dashboard ID: 7589 (Kafka 监控)

## 端口说明
- 3000: Grafana
- 9090: Prometheus
- 8082: cAdvisor
- 9100: Node Exporter
- 9308: Kafka Exporter
- 9116: ClickHouse Exporter

## 查看告警
Prometheus 告警页面: http://服务器IP:9090/alerts

## 卸载
```bash
docker-compose -f docker-compose.monitoring.yml down -v
```
