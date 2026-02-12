import json
import os
import traceback
import uuid
import requests
from flask import Flask, request, jsonify, redirect, make_response, Response
from config import PosthogConfig

app = Flask(__name__)


def load_password_store():
    if not os.path.exists(PosthogConfig.PASSWORD_FILE):
        with open(PosthogConfig.PASSWORD_FILE, "w") as f:
            f.write("{}")
    with open(PosthogConfig.PASSWORD_FILE, "r") as f:
        return json.load(f)


def save_password_store(store):
    with open(PosthogConfig.PASSWORD_FILE, "w") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def feishu_get_access_token(code):
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": PosthogConfig.FEISHU_CLIENT_ID,
        "client_secret": PosthogConfig.FEISHU_CLIENT_SECRET,
        "code": code,
        "redirect_uri": PosthogConfig.FEISHU_REDIRECT_URI
    }

    print(f"[飞书] 正在获取 access_token...")

    r = requests.post(
        PosthogConfig.FEISHU_TOKEN_URL,
        headers={"Content-Type": "application/json"},
        json=token_payload
    )

    print(f"[飞书] access_token 响应状态: {r.status_code}")
    print(f"[飞书] access_token 响应内容: {r.text}")

    return r.json()


def feishu_get_user_info(access_token):
    print(f"[飞书] 正在获取用户信息...")

    r = requests.get(
        PosthogConfig.FEISHU_USER_INFO_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    print(f"[飞书] 用户信息响应状态: {r.status_code}")
    print(f"[飞书] 用户信息响应内容: {r.text}")

    return r.json()


def posthog_admin_login():
    """PostHog 管理员登录，返回 session 和 CSRF token"""
    r = requests.post(
        f"{PosthogConfig.POSTHOG_URL}/api/login/",
        json={"email": PosthogConfig.ADMIN_EMAIL, "password": PosthogConfig.ADMIN_PASS}
    )
    print("[PostHog] 管理员登录响应:", r.status_code, r.text)

    if r.status_code == 200:
        sessionid = r.cookies.get('sessionid')
        csrf_token = r.cookies.get('posthog_csrftoken')
        return {"sessionid": sessionid, "csrf_token": csrf_token, "cookies": r.cookies}
    return None


def posthog_get_organization_id(admin_auth):
    """获取组织 ID"""
    r = requests.get(
        f"{PosthogConfig.POSTHOG_URL}/api/users/@me/",
        cookies=admin_auth["cookies"]
    )

    if r.status_code == 200:
        data = r.json()
        org_id = data.get("organization", {}).get("id")
        print(f"[PostHog] 获取到组织 ID: {org_id}")
        return org_id

    print(f"[PostHog] 获取组织 ID 失败: {r.status_code}")
    return None


def posthog_find_user(admin_session, email):
    """
    查找 PostHog 用户

    尝试登录来验证用户是否存在
    """
    r = requests.post(
        f"{PosthogConfig.POSTHOG_URL}/api/login",
        json={"email": email, "password": "dummy_password_test"}
    )

    print(f"[PostHog] 查找用户 {email} 响应: {r.status_code}")

    # 如果返回 200，说明密码正确（不太可能）
    # 如果返回 401/400 且有特定错误，说明用户存在
    if r.status_code in [200, 400, 401]:
        try:
            error_data = r.json()
            # 检查错误信息，判断是密码错误还是用户不存在
            if "password" in str(error_data).lower() or "credentials" in str(error_data).lower():
                return {"email": email, "exists": True}
        except:
            pass

    return None


def posthog_create_invite(admin_auth, org_id, email, name):
    """创建 PostHog 邀请"""
    first_name = name if name else "User"

    payload = {
        "target_email": email,
        "first_name": first_name,
        "level": 8,  # Member level
        "send_email": False  # 不发送邮件
    }

    print(f"[PostHog] 正在创建邀请给 {email}...")

    r = requests.post(
        f"{PosthogConfig.POSTHOG_URL}/api/organizations/{org_id}/invites/",
        cookies=admin_auth["cookies"],
        headers={"X-CSRFToken": admin_auth["csrf_token"]},
        json=payload
    )

    print(f"[PostHog] 创建邀请响应: {r.status_code}, {r.text}")

    if r.status_code in [200, 201]:
        invite_data = r.json()
        return invite_data

    return {"error": "create_invite_failed", "detail": r.text}


def posthog_create_user(admin_auth, email, name):
    """
    通过邀请机制创建 PostHog 用户

    1. 先获取组织 ID
    2. 创建邀请
    3. 使用邀请 ID 注册
    """
    org_id = posthog_get_organization_id(admin_auth)
    if not org_id:
        return {"error": "cannot_get_org_id"}

    # 创建邀请
    invite_data = posthog_create_invite(admin_auth, org_id, email, name)
    if "error" in invite_data:
        return invite_data

    invite_id = invite_data.get("id")
    if not invite_id:
        return {"error": "no_invite_id", "detail": invite_data}

    # 使用邀请注册用户
    first_name = name[0] if len(name) >= 1 else "User"
    last_name = name[1:] if len(name) >= 2 else ""
    random_password = "P" + str(uuid.uuid4()).replace("-", "")

    signup_payload = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": random_password
    }

    print(f"[PostHog] 正在通过邀请 {invite_id} 注册用户...")

    r = requests.post(
        f"{PosthogConfig.POSTHOG_URL}/api/signup/{invite_id}/",
        json=signup_payload
    )

    print(f"[PostHog] 注册用户响应: {r.status_code}, {r.text}")

    if r.status_code in [200, 201]:
        user_obj = r.json()
        user_obj["generated_password"] = random_password
        return user_obj

    return {"error": "signup_failed", "detail": r.text}


def posthog_user_login(email, password):
    """PostHog 用户登录"""
    r = requests.post(
        f"{PosthogConfig.POSTHOG_URL}/api/login/",
        json={"email": email, "password": password}
    )
    print("[PostHog] 用户登录响应:", r.status_code)

    if r.status_code == 200:
        return r.cookies.get('sessionid')
    return None


def posthog_validate_session(session_id):
    """验证 PostHog session"""
    if not session_id:
        return False

    try:
        r = requests.get(
            f"{PosthogConfig.POSTHOG_URL}/api/users/@me/",
            cookies={"sessionid": session_id},
            timeout=5
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[PostHog] 验证 session 异常: {e}")
        return False


def create_or_login_posthog_user(email, name):
    """
    创建或登录 PostHog 用户

    逻辑说明：
    1. 用户不存在 -> 通过邀请机制创建新用户
    2. 用户存在且 JSON 中有密码 -> 直接使用密码登录
    3. 用户存在但 JSON 中无密码 -> 自动重置密码并保存到 JSON
    """
    store = load_password_store()
    admin_auth = posthog_admin_login()

    if not admin_auth:
        print("[PostHog] 管理员登录失败")
        return {"error": "admin_login_failed"}

    user_obj = posthog_find_user(admin_auth, email)

    # 新用户：通过邀请机制创建
    if not user_obj:
        print(f"[PostHog] 用户不存在，正在创建新用户...")
        user_obj = posthog_create_user(admin_auth, email, name)

        if "error" in user_obj:
            return user_obj

        # 保存密码
        password = user_obj["generated_password"]
        store[email] = password
        save_password_store(store)

        # 用新密码登录获取 session
        session_id = posthog_user_login(email, password)
        if not session_id:
            return {"error": "login_after_signup_failed"}

        return {"session": session_id}

    # 已有用户
    else:
        if email not in store:
            print(f"[PostHog] 用户 {email} 密码丢失，正在自动重置密码...")

            # 生成新密码
            random_password = "P" + str(uuid.uuid4()).replace("-", "")

            # 获取用户 ID（需要从 user_obj 中获取）
            # 先通过 API 获取完整的用户信息
            r = requests.get(
                f"{PosthogConfig.POSTHOG_URL}/api/users/@me/",
                cookies=admin_auth["cookies"]
            )

            if r.status_code == 200:
                org_data = r.json()
                # 在组织成员中查找该用户
                r2 = requests.get(
                    f"{PosthogConfig.POSTHOG_URL}/api/organizations/{org_data['organization']['id']}/members/",
                    cookies=admin_auth["cookies"]
                )

                if r2.status_code == 200:
                    members = r2.json().get("results", [])
                    user_id = None
                    for member in members:
                        if member.get("user", {}).get("email", "").lower() == email.lower():
                            user_id = member.get("user", {}).get("id")
                            break

                    if user_id:
                        # 重置密码
                        reset_resp = requests.put(
                            f"{PosthogConfig.POSTHOG_URL}/api/user/{user_id}/password",
                            cookies=admin_auth["cookies"],
                            headers={"X-CSRFToken": admin_auth["csrf_token"]},
                            json={"password": random_password}
                        )

                        print(f"[PostHog] 密码重置响应状态: {reset_resp.status_code}")
                        print(f"[PostHog] 密码重置响应内容: {reset_resp.text}")

                        if reset_resp.status_code in [200, 204]:
                            # 保存新密码
                            store[email] = random_password
                            save_password_store(store)
                            password = random_password
                            print(f"[PostHog] 密码重置成功并已保存到 {PosthogConfig.PASSWORD_FILE}")
                        else:
                            print(f"[PostHog] 密码重置失败")
                            return {"error": "password_reset_failed", "detail": reset_resp.text}
                    else:
                        print(f"[PostHog] 未找到用户 ID")
                        return {"error": "user_id_not_found"}
                else:
                    print(f"[PostHog] 获取组织成员失败")
                    return {"error": "get_members_failed"}
            else:
                print(f"[PostHog] 获取组织信息失败")
                return {"error": "get_org_failed"}
        else:
            password = store[email]

    # 登录
    session_id = posthog_user_login(email, password)

    if not session_id:
        return {"error": "login_failed"}

    return {"session": session_id}


def proxy_to_posthog(path):
    """代理请求到 PostHog"""
    posthog_url = f"{PosthogConfig.POSTHOG_URL}/{path}"

    if request.query_string:
        posthog_url += f"?{request.query_string.decode('utf-8')}"

    print(f"[proxy] {request.method} {posthog_url}")

    try:
        headers = {k: v for k, v in request.headers if k.lower() != 'host'}

        if request.method == 'GET':
            resp = requests.get(
                posthog_url,
                headers=headers,
                cookies=request.cookies,
                allow_redirects=False,
                timeout=600
            )
        elif request.method == 'POST':
            resp = requests.post(
                posthog_url,
                headers=headers,
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                timeout=600
            )
        elif request.method == 'PUT':
            resp = requests.put(
                posthog_url,
                headers=headers,
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                timeout=600
            )
        elif request.method == 'DELETE':
            resp = requests.delete(
                posthog_url,
                headers=headers,
                cookies=request.cookies,
                allow_redirects=False,
                timeout=600
            )
        elif request.method == 'PATCH':
            resp = requests.patch(
                posthog_url,
                headers=headers,
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                timeout=600
            )
        elif request.method == 'OPTIONS':
            resp = requests.options(
                posthog_url,
                headers=headers,
                cookies=request.cookies,
                allow_redirects=False,
                timeout=600
            )
        elif request.method == 'HEAD':
            resp = requests.head(
                posthog_url,
                headers=headers,
                cookies=request.cookies,
                allow_redirects=False,
                timeout=600
            )
        else:
            print(f"[proxy错误] 不支持的 HTTP 方法: {request.method}")
            return Response("Method Not Allowed", status=405)

        excluded_headers = [
            'content-encoding', 'content-length', 'transfer-encoding',
            'connection', 'keep-alive', 'proxy-authenticate',
            'proxy-authorization', 'te', 'trailers', 'upgrade'
        ]

        response_headers = [
            (name, value) for (name, value) in resp.raw.headers.items()
            if name.lower() not in excluded_headers
        ]
        response = Response(
            resp.content,
            status=resp.status_code,
            headers=response_headers
        )

        # 转发 cookies
        for cookie in resp.cookies:
            response.set_cookie(
                cookie.name,
                cookie.value,
                path=cookie.path,
                domain=cookie.domain,
                secure=cookie.secure,
                httponly=cookie.has_nonstandard_attr('HttpOnly'),
                samesite=cookie.get_nonstandard_attr('SameSite', 'Lax')
            )

        return response

    except requests.exceptions.Timeout:
        print(f"[proxy] 请求超时: {posthog_url}")
        return Response("Gateway Timeout", status=504)
    except Exception as e:
        print(f"[proxy错误] {str(e)}")
        print(f"[proxy错误] 完整堆栈:\n{traceback.format_exc()}")
        return Response(f"Proxy Error: {str(e)}", status=502)


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "ok",
        "message": "pong",
        "service": "posthog-feishu-proxy"
    }), 200


# 飞书回调接口
@app.route("/feishu/redirect", methods=["GET"])
def feishu_redirect():
    code = request.args.get("code", "")
    state = request.args.get("state", "")

    print(f"[飞书回调] 收到 code: {code}")
    print(f"[飞书回调] 收到 state: {state}")

    if not code:
        return jsonify({"error": "missing_code"}), 400

    try:
        # 1. 获取access_token
        token_data = feishu_get_access_token(code)
        if token_data.get("code") != 0:
            return jsonify({
                "error": "feishu_token_failed",
                "detail": token_data
            }), 400

        access_token = token_data.get("access_token")
        if not access_token:
            return jsonify({
                "error": "access_token_not_found",
                "detail": token_data
            }), 400

        # 2. 获取用户信息
        user_info_data = feishu_get_user_info(access_token)

        if user_info_data.get("code") != 0:
            return jsonify({
                "error": "feishu_user_info_failed",
                "detail": user_info_data
            }), 400

        user_data = user_info_data.get("data", {})
        email = user_data.get("email")
        name = user_data.get("name")

        if not email:
            return jsonify({
                "error": "email_not_found",
                "detail": user_info_data
            }), 400

        print(f"[飞书] 获取到用户信息 - 姓名: {name}, 邮箱: {email}")

        # 3. 登录
        result = create_or_login_posthog_user(email, name)

        if "error" in result:
            return jsonify(result), 500

        session_id = result["session"]
        print(f"[PostHog] 创建会话成功: {session_id}")

        # 4. 设置 cookies 并重定向
        response = make_response(redirect(f"{PosthogConfig.EXTERNAL_DOMAIN}/"))

        response.set_cookie(
            "sessionid",
            session_id,
            path="/",
            httponly=True,
            secure=False,  # Nginx 到后端是 HTTP
            samesite="Lax",
            max_age=60 * 60 * 24 * 7  # 7天
        )

        print(f"[授权成功后重定向] 正在跳转到 {PosthogConfig.EXTERNAL_DOMAIN}/ 并设置 session cookie")
        print(f"[授权成功后重定向] sessionid = {session_id}")

        return response

    except Exception as e:
        print(f"[错误] 飞书登录流程异常: {str(e)} \n{traceback.format_exc()}")
        return jsonify({
            "error": "internal_error",
            "detail": str(e)
        }), 500


# 统一请求拦截器
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def catch_all(path):
    """
    拦截所有请求，检查是否已登录

    1. 白名单路径（埋点、API）-> 直接转发，不检查登录
    2. 未登录 -> 重定向到飞书 OAuth
    3. 已登录 -> 转发请求到 PostHog
    """

    # 白名单：这些路径不需要检查登录，直接转发
    # 参考 PostHog Caddy 配置
    WHITELIST_PATHS = [
        # 事件采集
        'e',           # /e - 事件上报
        'e/',
        'i/v0',        # /i/v0 - 数据采集
        'i/v0/',
        'i/v0/ai',     # /i/v0/ai - AI 采集
        'i/v0/ai/',
        'i/v1/logs',   # /i/v1/logs - 日志采集
        'i/v1/logs/',
        'batch',       # /batch - 批量上报
        'batch/',
        'capture',     # /capture - 捕获事件
        'capture/',

        # Session 录制
        's',           # /s - Session 录制
        's/',

        # 功能开关
        'flags',       # /flags - 功能开关
        'flags/',
        'decide',      # /decide - 决策 API
        'decide/',

        # Webhooks
        'public/webhooks',
        'public/webhooks/',
        'public/m/',

        # Livestream
        'livestream',
        'livestream/',

        # 静态资源
        'static/',
        '_next/',      # Next.js 静态资源
        'assets/',
    ]

    # 检查是否是白名单路径
    for whitelist in WHITELIST_PATHS:
        if path.startswith(whitelist):
            print(f"[拦截器] 白名单路径，直接转发: /{path}")
            return proxy_to_posthog(path)

    if path.startswith('feishu/'):
        print(f"[拦截器] 跳过飞书回调路径: {path}")
        return jsonify({"error": "route_not_found"}), 404

    session_id = request.cookies.get("sessionid")

    print(f"[拦截器] 请求来源: {request.headers.get('Host')}")
    print(f"[拦截器] 路径: /{path}")
    print(f"[拦截器] 所有 Cookies: {dict(request.cookies)}")
    print(f"[拦截器] sessionid: {session_id[:20] if session_id else 'None'}...")

    if not posthog_validate_session(session_id):
        print(f"[拦截器] Session 无效或不存在，正在重定向到飞书登录")

        feishu_auth_url = (
            f"https://open.feishu.cn/open-apis/authen/v1/index"
            f"?app_id={PosthogConfig.FEISHU_CLIENT_ID}"
            f"&redirect_uri={PosthogConfig.FEISHU_REDIRECT_URI}"
            f"&state=posthog_auth"
        )

        return redirect(feishu_auth_url)

    print(f"[拦截器] Session 有效，正在转发请求到 PostHog")
    return proxy_to_posthog(path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PosthogConfig.PORT)
