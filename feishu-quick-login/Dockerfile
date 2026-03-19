FROM uhub.service.ucloud.cn/deeplang/python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用代码
COPY app.py .

# 创建配置文件目录
RUN mkdir -p /app

EXPOSE 5000

CMD ["python", "app.py"]
