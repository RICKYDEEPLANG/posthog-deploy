from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/eb3f5dc2-8187-45e0-8b4c-303f6c0be200"

@app.route('/webhook', methods=['POST'])
def alertmanager_webhook():
    data = request.json

    for alert in data.get('alerts', []):
        status = alert.get('status')
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})

        # 根据告警级别设置颜色和图标
        if labels.get('severity') == 'critical':
            color = "red"
            icon = "🔴"
        else:
            color = "orange"
            icon = "🟠"

        # 状态显示
        status_text = "🚨 触发" if status == "firing" else "✅ 恢复"

        # 构造飞书卡片消息
        feishu_msg = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{icon} PostHog 告警: {labels.get('alertname', 'Unknown')}"
                    },
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**状态**: {status_text}\n**严重程度**: {labels.get('severity', 'unknown')}\n**摘要**: {annotations.get('summary', 'N/A')}\n**详情**: {annotations.get('description', 'N/A')}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"触发时间: {alert.get('startsAt', 'N/A')}"
                            }
                        ]
                    }
                ]
            }
        }

        # 发送到飞书
        try:
            response = requests.post(FEISHU_WEBHOOK, json=feishu_msg, timeout=5)
            print(f"[{datetime.now()}] Sent alert to Feishu: {response.status_code} - {labels.get('alertname')}")
            if response.status_code != 200:
                print(f"Error response: {response.text}")
        except Exception as e:
            print(f"[{datetime.now()}] Error sending to Feishu: {e}")

    return jsonify({"status": "ok"}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
