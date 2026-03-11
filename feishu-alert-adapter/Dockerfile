FROM uhub.service.ucloud.cn/deeplang/python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
