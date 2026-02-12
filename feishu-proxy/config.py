class PosthogConfig:
    # PostHog 配置
    POSTHOG_URL = "http://proxy:80"  # 通过 Caddy 代理，不是直接连 web
    ADMIN_EMAIL = "yajun.chen@deeplang.ai"
    ADMIN_PASS = "TydhU7BC2bVTnBm"
    PASSWORD_FILE = "/app/pwd.json"  # Docker 容器内路径

    # 外部访问域名
    EXTERNAL_DOMAIN = "https://posthog.deeplang.tech"

    # 飞书应用配置
    FEISHU_CLIENT_ID = "cli_a90736d6c9389cb1"
    FEISHU_CLIENT_SECRET = "VnWSzOIi8SfGXdTCUeROGeJu5iGhjBDB"
    FEISHU_REDIRECT_URI = f"{EXTERNAL_DOMAIN}/feishu/redirect"
    FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    FEISHU_USER_INFO_URL = "https://open.feishu.cn/open-apis/authen/v1/user_info"

    # 代理服务端口
    PORT = 8910
