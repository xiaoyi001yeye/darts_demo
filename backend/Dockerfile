FROM python:3.10-slim AS builder
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com && \
    pip config set global.timeout 120 && \
    pip config set install.retries 5

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir u8darts[all] --default-timeout=120 --retries 5 && \
    pip install --no-cache-dir -r requirements.txt --default-timeout=120 --retries 5 

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包含科学计算所需的库）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    pkg-config \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 复制数据文件到容器中
COPY data/tb_metric_raw_free_space_ratio_202509161435.csv /app/data/

# 暴露端口
EXPOSE 5001

# 设置环境变量
ENV DATA_DIR=/app/data
ENV PYTHONPATH=/app
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

# 启动命令
CMD ["python", "app.py"]