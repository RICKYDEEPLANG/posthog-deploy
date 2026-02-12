#!/usr/bin/env python3
"""
测试 PostHog 邀请机制
"""
import requests
import uuid

POSTHOG_URL = "https://posthog.deeplang.tech"
ADMIN_EMAIL = "yajun.chen@deeplang.ai"
ADMIN_PASS = "TydhU7BC2bVTnBm"
TEST_EMAIL = f"test-{uuid.uuid4().hex[:8]}@deeplang.ai"
TEST_NAME = "测试用户"

print("=" * 60)
print("测试 PostHog 邀请机制")
print("=" * 60)

# 1. 管理员登录
print("\n[1] 管理员登录...")
r = requests.post(
    f"{POSTHOG_URL}/api/login",
    json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}
)
print(f"   状态码: {r.status_code}")
print(f"   响应: {r.text}")

if r.status_code != 200:
    print("❌ 管理员登录失败")
    exit(1)

admin_cookies = r.cookies
print("✅ 管理员登录成功")

# 2. 获取组织 ID
print("\n[2] 获取组织 ID...")
r = requests.get(
    f"{POSTHOG_URL}/api/users/@me/",
    cookies=admin_cookies
)
print(f"   状态码: {r.status_code}")

if r.status_code != 200:
    print("❌ 获取用户信息失败")
    exit(1)

data = r.json()
org_id = data.get("organization", {}).get("id")
print(f"✅ 组织 ID: {org_id}")

# 3. 创建邀请
print(f"\n[3] 创建邀请给 {TEST_EMAIL}...")

# 获取 CSRF token
csrf_token = admin_cookies.get("posthog_csrftoken")
print(f"   CSRF Token: {csrf_token[:20] if csrf_token else 'None'}...")

r = requests.post(
    f"{POSTHOG_URL}/api/organizations/{org_id}/invites/",
    cookies=admin_cookies,
    headers={"X-CSRFToken": csrf_token} if csrf_token else {},
    json={
        "target_email": TEST_EMAIL,
        "first_name": TEST_NAME,
        "level": 8,  # Member
        "send_email": False
    }
)
print(f"   状态码: {r.status_code}")
print(f"   响应: {r.text}")

if r.status_code not in [200, 201]:
    print("❌ 创建邀请失败")
    exit(1)

invite_data = r.json()
invite_id = invite_data.get("id")
print(f"✅ 邀请创建成功，ID: {invite_id}")

# 4. 使用邀请注册用户
print(f"\n[4] 使用邀请 {invite_id} 注册用户...")
test_password = f"TestPass{uuid.uuid4().hex[:8]}"
r = requests.post(
    f"{POSTHOG_URL}/api/signup/{invite_id}/",
    json={
        "email": TEST_EMAIL,
        "first_name": "测试",
        "last_name": "用户",
        "password": test_password
    }
)
print(f"   状态码: {r.status_code}")
print(f"   响应: {r.text}")

if r.status_code not in [200, 201]:
    print("❌ 注册用户失败")
    exit(1)

print("✅ 用户注册成功")

# 5. 用新用户登录
print(f"\n[5] 用新用户登录...")
r = requests.post(
    f"{POSTHOG_URL}/api/login",
    json={"email": TEST_EMAIL, "password": test_password}
)
print(f"   状态码: {r.status_code}")
print(f"   响应: {r.text}")

if r.status_code != 200:
    print("❌ 新用户登录失败")
    exit(1)

user_cookies = r.cookies
sessionid = user_cookies.get("sessionid")
print(f"✅ 新用户登录成功，sessionid: {sessionid[:20]}...")

# 6. 验证 session
print(f"\n[6] 验证 session...")
r = requests.get(
    f"{POSTHOG_URL}/api/users/@me/",
    cookies=user_cookies
)
print(f"   状态码: {r.status_code}")

if r.status_code != 200:
    print("❌ Session 验证失败")
    exit(1)

user_data = r.json()
print(f"✅ Session 有效，用户: {user_data.get('email')}")

print("\n" + "=" * 60)
print("🎉 所有测试通过！邀请机制工作正常")
print("=" * 60)
print(f"\n测试账号信息：")
print(f"  邮箱: {TEST_EMAIL}")
print(f"  密码: {test_password}")
print(f"  Session ID: {sessionid}")
