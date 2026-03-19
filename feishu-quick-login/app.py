from flask import Flask, redirect, request
import requests
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
POSTHOG_URL = os.getenv("POSTHOG_URL", "http://web:8000")
POSTHOG_EXTERNAL_URL = os.getenv("POSTHOG_EXTERNAL_URL", "https://posthog.deeplang.tech")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/callback")

def load_users():
    """从配置文件加载用户映射"""
    try:
        with open('/app/users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"example@company.com": "changeme"}

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
        logger.error("飞书回调缺少code参数")
        return "缺少code参数", 400

    try:
        # 1. 获取access_token
        token_resp = requests.post(
            'https://open.feishu.cn/open-apis/authen/v1/access_token',
            json={"grant_type": "authorization_code", "code": code},
            headers={"Authorization": f"Bearer {get_app_access_token()}"}
        )

        if token_resp.status_code != 200 or token_resp.json().get('code') != 0:
            logger.error(f"飞书认证失败: {token_resp.text}")
            return f"飞书认证失败: {token_resp.text}", 400

        access_token = token_resp.json()['data']['access_token']

        # 2. 获取用户邮箱
        user_resp = requests.get(
            'https://open.feishu.cn/open-apis/authen/v1/user_info',
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_resp.status_code != 200 or user_resp.json().get('code') != 0:
            logger.error(f"获取用户信息失败: {user_resp.text}")
            return f"获取用户信息失败: {user_resp.text}", 400

        email = user_resp.json()['data'].get('email') or user_resp.json()['data'].get('enterprise_email')

        if not email:
            logger.error("未获取到用户邮箱")
            return "未获取到用户邮箱，请确保飞书应用有邮箱权限", 400

        # 3. 查找PostHog密码
        users = load_users()
        password = users.get(email)

        if not password:
            logger.error(f"用户 {email} 未配置")
            return f"用户 {email} 未配置PostHog访问权限", 403

        # 4. 调用PostHog登录API
        session = requests.Session()
        login_resp = session.post(
            f'{POSTHOG_URL}/api/login/',
            json={'email': email, 'password': password},
            allow_redirects=False
        )

        if login_resp.status_code not in [200, 204]:
            logger.error(f"PostHog登录失败 ({login_resp.status_code}): {login_resp.text[:200]}")
            return f"PostHog登录失败: {login_resp.text}", 400

        # 5. 获取cookie
        sessionid = session.cookies.get('sessionid')
        csrftoken = session.cookies.get('csrftoken')

        if not sessionid:
            logger.error("未获取到sessionid")
            return "未获取到PostHog会话", 500

        logger.info(f"✓ 用户 {email} 登录成功")

        # 6. 返回HTML设置cookie并跳转
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>登录中...</title>
            <style>
                body {{ font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
                .box {{ text-align: center; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .spinner {{ border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div class="box">
                <h2>登录成功！</h2>
                <div class="spinner"></div>
                <p>正在跳转...</p>
            </div>
            <script>
                document.cookie = "sessionid={sessionid}; path=/; max-age=1209600; SameSite=Lax";
                document.cookie = "csrftoken={csrftoken}; path=/; max-age=31449600; SameSite=Lax";
                setTimeout(() => window.location.href = '{POSTHOG_EXTERNAL_URL}', 1000);
            </script>
        </body>
        </html>
        """

    except Exception as e:
        logger.exception(f"异常: {str(e)}")
        return f"登录异常: {str(e)}", 500

def get_app_access_token():
    """获取飞书app_access_token"""
    resp = requests.post(
        'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal',
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    )

    if resp.status_code != 200 or resp.json().get('code') != 0:
        raise Exception(f"获取app_access_token失败: {resp.text}")

    return resp.json()['app_access_token']

@app.route('/health')
def health():
    """健康检查"""
    return {"status": "ok", "service": "feishu-quick-login"}

if __name__ == '__main__':
    logger.info(f"启动飞书快捷登录服务 - POSTHOG_URL: {POSTHOG_URL}, REDIRECT_URI: {REDIRECT_URI}")
    app.run(host='0.0.0.0', port=5000, debug=False)
