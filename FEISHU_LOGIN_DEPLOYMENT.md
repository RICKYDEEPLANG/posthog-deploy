# PostHog 飞书快捷登录 - 部署指南

## 快速部署步骤

### 1. 构建并启动服务

```bash
cd /path/to/posthog

# 构建镜像
docker-compose -f docker-compose.feishu-login.yml build

# 启动服务
docker-compose -f docker-compose.feishu-login.yml up -d
```

### 2. 验证服务运行

```bash
# 检查容器状态
docker ps | grep feishu-quick-login

# 查看日志
docker logs posthog-feishu-quick-login

# 健康检查
curl http://localhost:5000/health
```

### 3. 配置反向代理（重要！）

#### 如果使用 Caddy：

将 `Caddyfile.feishu` 内容添加到你的 Caddy 配置中，或者：

```bash
# 替换现有 Caddyfile
cp Caddyfile.feishu /etc/caddy/Caddyfile

# 重启 Caddy
docker restart caddy
# 或
systemctl reload caddy
```

#### 如果使用 Nginx：

添加以下配置到 nginx.conf：

```nginx
server {
    listen 443 ssl;
    server_name posthog.deeplang.tech;

    # 飞书登录路径
    location /feishu-login {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # PostHog 主服务
    location / {
        proxy_pass http://posthog-web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. 测试登录流程

1. 访问：`https://posthog.deeplang.tech/feishu-login`
2. 应该会自动跳转到飞书登录页面
3. 飞书登录成功后，自动跳转回PostHog并已登录

### 5. 添加更多用户

编辑 `feishu-quick-login/users.json`：

```bash
vim feishu-quick-login/users.json
```

添加用户：

```json
{
  "yajun.chen@deeplang.ai": "TydhU7BC2bVTnBm",
  "newuser@deeplang.ai": "newuser_password"
}
```

重启服务：

```bash
docker-compose -f docker-compose.feishu-login.yml restart
```

## 故障排查

### 问题1: 飞书认证失败

**检查项：**
- 飞书应用的 App ID 和 App Secret 是否正确
- 飞书应用的重定向URL是否配置为：`https://posthog.deeplang.tech/feishu-login/callback`
- 飞书应用是否已申请邮箱权限并通过审核

**查看日志：**
```bash
docker logs -f posthog-feishu-quick-login
```

### 问题2: PostHog登录失败

**检查项：**
- users.json 中的邮箱和密码是否正确
- PostHog服务是否正常运行
- 网络连接是否正常

**测试PostHog登录API：**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"yajun.chen@deeplang.ai","password":"TydhU7BC2bVTnBm"}'
```

### 问题3: Cookie未设置

**检查项：**
- 反向代理配置是否正确
- 飞书登录服务和PostHog是否在同一个域名下
- 浏览器控制台是否有cookie设置错误

### 问题4: 404 Not Found

**检查项：**
- 反向代理配置中 `/feishu-login` 路径是否正确配置
- 服务端口5000是否已暴露

## 安全建议

1. **users.json 权限**：
   ```bash
   chmod 600 feishu-quick-login/users.json
   ```

2. **不要提交密码到git**：
   users.json 已在 .gitignore 中，确保不会被提交

3. **定期更换密码**：
   建议定期更新 users.json 中的密码

4. **监控登录日志**：
   ```bash
   docker logs -f posthog-feishu-quick-login
   ```

## 维护

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建
docker-compose -f docker-compose.feishu-login.yml build

# 重启服务
docker-compose -f docker-compose.feishu-login.yml up -d
```

### 停止服务

```bash
docker-compose -f docker-compose.feishu-login.yml down
```

### 查看实时日志

```bash
docker logs -f posthog-feishu-quick-login
```
