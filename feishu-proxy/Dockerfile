FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

COPY . .

# 创建密码存储文件
RUN touch /app/pwd.json && echo '{}' > /app/pwd.json

EXPOSE 8910

CMD ["python", "posthog_proxy.py"]
