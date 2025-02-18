# 使用官方 Python 3.12 slim镜像
FROM python:3.12-slim

# 设置 pip 国内源为腾讯源
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖，清理缓存以减小镜像大小
RUN pip install --no-cache-dir -r requirements.txt

# 设置默认命令
CMD ["python", "/app/ddns.py"]
