# PostHog 飞书登录代理

为 PostHog 提供飞书 OAuth 登录功能的代理服务。

## 功能说明

1. **飞书 OAuth 认证**：拦截所有请求，未认证用户重定向到飞书登录
2. **自动用户管理**：
   - 新用户：自动在 PostHog 创建账号并生成随机密码
   - 已有用户：使用本地 JSON 存储的密码登录
3. **透明代理**：已认证用户的所有请求透明转发到 PostHog 服务

## 配置说明

### 飞书应用配置
- **App ID**: `cli_a90736d6c9389cb1`
- **App Secret**: `VnWSzOIi8SfGXdTCUeROGeJu5iGhjBDB`
- **回调地址**: `https://posthog.deeplang.tech/feishu/redirect`

### PostHog 配置
- **内部地址**: `http://web:8000`（Docker 内部网络）
- **外部域名**: `https://posthog.deeplang.tech`
- **管理员账号**: `yajun.chen@deeplang.ai`
- **代理端口**: `8910`

## 部署方式

### 1. 启动服务

在 PostHog 项目根目录执行：

```bash
docker-compose up -d feishu-proxy
```

或重新启动所有服务：

```bash
docker-compose up -d
```

### 2. 配置域名解析

将 `posthog.deeplang.tech` 解析到服务器的 `8910` 端口：

```
posthog.deeplang.tech  ->  服务器IP:8910
```

### 3. 验证服务

访问健康检查接口：

```bash
curl http://localhost:8910/ping
```

应返回：

```json
{
  "status": "ok",
  "message": "pong",
  "service": "posthog-feishu-proxy"
}

```

## 使用流程

1. 用户访问 `https://posthog.deeplang.tech/`
2. 未登录用户自动跳转到飞书授权页面
3. 用户在飞书完成授权
4. 回调到代理服务，自动创建/登录 PostHog 账号
5. 设置 session cookie 并重定向到 PostHog 首页
6. 后续请求透明代理到 PostHog

## 查看日志

```bash
docker-compose logs -f feishu-proxy
```

## 密码存储

用户密码保存在 Docker volume `feishu-proxy-data` 中的 `pwd.json` 文件。

## 注意事项

1. **HTTPS 要求**：飞书回调需要 HTTPS，请确保域名配置了 SSL 证书
2. **Cookie 安全**：sessionid cookie 设置了 `secure=True` 和 `httponly=True`
3. **密码管理**：首次登录时自动生成随机密码，如密码丢失需联系管理员

## 文件结构

```
feishu-proxy/
├── config.py              # 配置文件
├── posthog_proxy.py       # 主程序
├── requirements.txt       # Python 依赖
├── Dockerfile            # Docker 镜像构建
├── .dockerignore         # Docker 忽略文件
├── pwd.json              # 用户密码存储（自动生成）
└── README.md             # 说明文档
```

## 故障排查

### 问题 1：无法访问飞书回调地址

检查域名解析是否正确：

```bash
nslookup posthog.deeplang.tech
```

### 问题 2：登录后仍然跳转到飞书

检查 session cookie 是否正确设置，查看浏览器开发者工具 > Application > Cookies

### 问题 3：创建用户失败

查看容器日志确认 PostHog API 返回的错误信息：

```bash
docker-compose logs feishu-proxy
```
