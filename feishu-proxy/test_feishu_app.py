#!/usr/bin/env python3
"""
测试飞书应用配置
"""
import requests

FEISHU_CLIENT_ID = "cli_a90736d6c9389cb1"
FEISHU_CLIENT_SECRET = "VnWSzOIi8SfGXdTCUeROGeJu5iGhjBDB"
FEISHU_REDIRECT_URI = "https://posthog.deeplang.tech/feishu/redirect"

print("=" * 60)
print("测试飞书应用配置")
print("=" * 60)

# 1. 测试飞书授权 URL
print("\n[1] 飞书授权 URL:")
auth_url = (
    f"https://open.feishu.cn/open-apis/authen/v1/index"
    f"?app_id={FEISHU_CLIENT_ID}"
    f"&redirect_uri={FEISHU_REDIRECT_URI}"
    f"&state=test123"
)
print(f"   {auth_url}")
print("   ✅ 请在浏览器中打开这个 URL 测试")

# 2. 测试 Client ID 和 Secret 是否有效
print("\n[2] 测试 Client ID 和 Secret...")
print("   尝试获取 app_access_token...")

r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
    json={
        "app_id": FEISHU_CLIENT_ID,
        "app_secret": FEISHU_CLIENT_SECRET
    }
)

print(f"   状态码: {r.status_code}")
print(f"   响应: {r.text}")

if r.status_code == 200:
    data = r.json()
    if data.get("code") == 0:
        print("   ✅ Client ID 和 Secret 有效")
    else:
        print(f"   ❌ 飞书返回错误: {data}")
else:
    print(f"   ❌ 请求失败")

# 3. 检查回调地址配置
print("\n[3] 回调地址配置:")
print(f"   配置的回调地址: {FEISHU_REDIRECT_URI}")
print("   ⚠️  请确认在飞书开放平台配置了这个回调地址")
print("   飞书开放平台: https://open.feishu.cn/app")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
