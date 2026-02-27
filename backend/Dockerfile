# 支持多架构构建
FROM --platform=$BUILDPLATFORM ubuntu:20.04

# 声明构建参数
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG TARGETARCH

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.13.1

# 安装基础依赖和系统工具
RUN apt update && apt install -y \
    wget \
    build-essential \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    curl \
    git \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libxrandr2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# 根据架构选择合适的编译参数安装Python
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        export CONFIGURE_OPTS="--enable-optimizations --build=aarch64-linux-gnu"; \
    else \
        export CONFIGURE_OPTS="--enable-optimizations"; \
    fi && \
    wget https://mirrors.huaweicloud.com/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz && \
    tar -xf Python-${PYTHON_VERSION}.tar.xz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure $CONFIGURE_OPTS && \
    make -j$(nproc) && \
    make altinstall && \
    cd .. && \
    rm -rf Python-${PYTHON_VERSION}.tar.xz Python-${PYTHON_VERSION}

# 创建Python符号链接
RUN ln -s /usr/local/bin/python3.13 /usr/local/bin/python3 && \
    ln -s /usr/local/bin/pip3.13 /usr/local/bin/pip3 && \
    ln -s /usr/local/bin/python3.13 /usr/local/bin/python

# 安装Node.js和pnpm (用于前端构建工具)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt install -y nodejs && \
    npm install -g pnpm && \
    rm -rf /var/lib/apt/lists/*

# 根据架构安装不同的 Firefox 包和依赖
RUN apt update --fix-missing && \
    if [ "$TARGETARCH" = "arm64" ]; then \
        # 对于 arm64 架构，尝试安装 firefox 或使用其他浏览器
        apt install -y --no-install-recommends firefox || \
        (echo "Firefox not available for arm64, installing alternatives..." && \
         apt install -y --no-install-recommends chromium-browser) || \
        echo "Browser installation skipped for arm64"; \
    else \
        # 对于 x86_64 架构，安装标准 Firefox
        apt install -y --no-install-recommends firefox firefox-esr; \
    fi && \
    apt install -y --no-install-recommends \
        fonts-liberation \
        fonts-noto-color-emoji \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libxtst6 \
        && apt clean && apt autoremove -y && rm -rf /var/lib/apt/lists/*

# 自动设置时区（上海）
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 设置工作目录
WORKDIR /app

# 复制Python依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 安装Playwright并下载浏览器
RUN playwright install && \
    playwright install firefox && \
    playwright install-deps

# 复制应用代码
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/cache

# 暴露端口
EXPOSE 38001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:38001/api/docs || exit 1

# 启动脚本
CMD ["/entrypoint.sh"]
