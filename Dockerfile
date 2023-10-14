FROM python:3.11.4-slim-bullseye as base

# 替换为阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
  gcc \
  && rm -rf /var/lib/apt/lists/*

# 将 pip 镜像源设置为阿里云
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

RUN pip install poetry==1.6.1
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc

# Configuring poetry
RUN poetry config virtualenvs.create false

# Copying requirements of a project
COPY pyproject.toml poetry.lock /app/src/
WORKDIR /app/src

# 安装项目
RUN poetry install --only main

# Removing gcc
RUN apt-get purge -y \
  gcc \
  && rm -rf /var/lib/apt/lists/*

# 拷贝项目代码设置工作目录
COPY . /app/src/
RUN poetry install --only main

CMD ["/usr/local/bin/python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS collector

# 安装守护进程工具
RUN pip install supervisor