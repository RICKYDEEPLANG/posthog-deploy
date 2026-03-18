from flask import Flask, redirect, request, render_template_string
import requests
import os
import json

app = Flask(__name__)

# 配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
POSTHOG_URL = os.getenv("POSTHOG_URL", "http://posthog-web:8000")  # PostHog内部地址
POSTHOG_EXTERNAL_URL = os.getenv("POSTHOG_EXTERNAL_URL", "https://posthog.deeplang.tech")  # PostHog外部地址
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/callback")

# 用户映射（邮箱 -> PostHog密码）
def load_users():
    """从配置文件加载用户映射"""
    try:
        with open('/app/users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果配置文件不存在，使用默认配置
        return {
            "example@company.com": "changeme"
        }

@app.route('/')
def index():
    """飞书登录入口"""
    feishu_auth_url = (
        f"https://open.feishu.cn/open-apis/authen/v1/index"
        f"?app_id={FEISHU_APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return redirect(feishu_auth_url)

@app.route('/callback')
def callback():
    """飞书OAuth回调"""
    code = request.args.get('code')

    if not code:
        return "缺少code参数", 400

    # 1. 用code换取access_token
    try:
        token_resp = requests.post(
            'https://open.feishu.cn/open-apis/authen/v1/access_token',
            json={
                "grant_type": "authorization_code",
                "code": code
            },
            headers={
                "Authorization": f"Bearer {get_app_access_token()}"
            }
        )

        if token_resp.status_code != 200:
            return f"飞书认证失败: {token_resp.text}", 400

        token_data = token_resp.json()
        if token_data.get('code') != 0:
            return f"飞书认证失败: {token_data.get('msg')}", 400

        access_token = token_data['data']['access_token']

    except Exception as e:
        return f"飞书认证异常: {str(e)}", 500

    # 2. 获取用户信息（邮箱）
    try:
        user_resp = requests.get(
            'https://open.feishu.cn/open-apis/authen/v1/user_info',
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_resp.status_code != 200:
            return f"获取用户信息失败: {user_resp.text}", 400

        user_data = user_resp.json()
        if user_data.get('code') != 0:
            return f"获取用户信息失败: {user_data.get('msg')}", 400

        email = user_data['data'].get('email') or user_data['data'].get('enterprise_email')

        if not email:
            return "未获取到用户邮箱，请确保飞书应用有邮箱权限", 400

    except Exception as e:
        return f"获取用户信息异常: {str(e)}", 500

    # 3. 查找PostHog密码
    users = load_users()
    password = users.get(email)

    if not password:
        return f"用户 {email} 未配置PostHog访问权限<br><br>请联系管理员在 users.json 中添加该用户", 403

    # 4. 调用PostHog登录API
    try:
        session = requests.Session()
        login_resp = session.post(
            f'{POSTHOG_URL}/api/login/',
            json={'email': email, 'password': password},
            allow_redirects=False
        )

        if login_resp.status_code not in [200, 204]:
            return f"PostHog登录失败 ({login_resp.status_code}): {login_resp.text}", 400

    except Exception as e:
        return f"PostHog登录异常: {str(e)}", 500

    # 5. 获取session cookie
    sessionid = session.cookies.get('sessionid')
    csrftoken = session.cookies.get('csrftoken')

    if not sessionid:
        return "未获取到PostHog会话，请检查PostHog服务状态", 500

    # 6. 返回HTML，自动设置cookie并跳转
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>登录中...</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }}
            .container {{
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h2 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>登录成功！</h2>
            <div class="spinner"></div>
            <p>正在跳转到 PostHog...</p>
        </div>
        <script>
            // 设置cookie
            document.cookie = "sessionid={sessionid}; path=/; max-age=1209600; SameSite=Lax";
            document.cookie = "csrftoken={csrftoken}; path=/; max-age=31449600; SameSite=Lax";

            // 跳转到PostHog
            setTimeout(function() {{
                window.location.href = '{POSTHOG_EXTERNAL_URL}';
            }}, 1000);
        </script>
    </body>
    </html>
    """

    return html

def get_app_access_token():
    """获取飞书应用access_token"""
    resp = requests.post(
        'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal',
        json={
            "app_id": FEISHU_APP_ID,
            "app_secret": FEISHU_APP_SECRET
        }
    )

    if resp.status_code != 200:
        raise Exception(f"获取app_access_token失败: {resp.text}")

    data = resp.json()
    if data.get('code') != 0:
        raise Exception(f"获取app_access_token失败: {data.get('msg')}")

    return data['app_access_token']

@app.route('/health')
def health():
    """健康检查"""
    return {"status": "ok", "service": "feishu-quick-login"}

if __name__ == '__main__':
    # 检查必需的环境变量
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print("警告: 未设置 FEISHU_APP_ID 或 FEISHU_APP_SECRET")

    app.run(host='0.0.0.0', port=5000, debug=False)
