# PostHog 飞书快捷登录服务

## 功能说明

提供飞书OAuth快捷登录PostHog的功能，员工通过飞书认证后自动登录PostHog，无需手动输入密码。

## 工作流程

1. 用户访问 `http://your-domain/feishu-login`
2. 自动跳转到飞书OAuth认证
3. 飞书认证成功后，服务获取用户邮箱
4. 根据邮箱查找对应的PostHog密码（从users.json）
5. 调用PostHog登录API获取session
6. 返回HTML页面自动设置cookie并跳转到PostHog

## 配置步骤

### 1. 创建飞书应用

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 App ID 和 App Secret
4. 配置重定向URL：`http://your-domain/feishu-login/callback`
5. 申请权限：`获取用户邮箱信息`

### 2. 配置用户映射

编辑 `users.json` 文件，添加飞书邮箱和PostHog密码的映射：

```json
{
  "employee1@company.com": "posthog_password_1",
  "employee2@company.com": "posthog_password_2"
}
```

### 3. 设置环境变量

在 `docker-compose.yml` 中配置：

```yaml
environment:
  - FEISHU_APP_ID=你的飞书AppID
  - FEISHU_APP_SECRET=你的飞书AppSecret
  - POSTHOG_URL=http://posthog-web:8000
  - REDIRECT_URI=http://your-domain/feishu-login/callback
```

### 4. 启动服务

```bash
docker-compose up -d feishu-quick-login
```

## 使用方法

员工访问：`http://your-domain/feishu-login`

即可通过飞书快捷登录PostHog。

## 注意事项

1. **安全性**：users.json 存储密码，请确保文件权限安全，不要提交到git仓库
2. **域名配置**：需要确保飞书登录服务和PostHog在同一个域名下（通过Caddy反向代理）
3. **埋点不受影响**：此服务仅用于Web登录，不影响埋点API调用
4. **新员工入职**：在 users.json 中添加对应的邮箱和密码即可

## API端点

- `GET /` - 飞书登录入口
- `GET /callback` - 飞书OAuth回调
- `GET /health` - 健康检查

## 故障排查

### 登录失败

1. 检查飞书应用配置是否正确
2. 检查 users.json 中是否有该用户的配置
3. 检查PostHog密码是否正确
4. 查看容器日志：`docker logs posthog-feishu-quick-login`

### Cookie未设置

检查域名配置，确保飞书登录服务和PostHog使用相同的域名。
