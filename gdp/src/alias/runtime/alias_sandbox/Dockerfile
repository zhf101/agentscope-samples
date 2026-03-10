FROM node:22-slim

# Base runtime knobs used by app and scripts.
ENV NODE_ENV=production
ENV WORKSPACE_DIR=/workspace

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --fix-missing \
    curl  \
    python3  \
    python3-pip  \
    python3-venv \
    build-essential  \
    libssl-dev  \
    git  \
    supervisor  \
    vim  \
    nginx \
    gettext-base \
    xfce4 \
    xfce4-terminal \
    x11vnc \
    xvfb \
    novnc \
    websockify \
    dbus-x11 \
    fonts-wqy-zenhei \
    fonts-wqy-microhei

# Browser runtime dependencies for Chromium + automation.
RUN apt-get update && apt-get install -y --fix-missing \
    chromium \
    chromium-sandbox \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libglib2.0-0 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    libu2f-udev

RUN apt-get update && apt-get install -y --fix-missing \
    wget \
    grep \
    findutils

RUN sed -i 's/^CHROMIUM_FLAGS=""/CHROMIUM_FLAGS="--no-sandbox"/' /usr/bin/chromium

# Install agent-browser CLI (Vercel's AI-optimized browser automation tool)
RUN npm install -g agent-browser && \
    agent-browser install

# Python service code and dependencies live under /agentscope_runtime.
WORKDIR /agentscope_runtime
RUN python3 -m venv venv
ENV PATH="/agentscope_runtime/venv/bin:$PATH"

COPY box/ ./

RUN pip install -r requirements.txt

# Workspace is the mutable area exposed via API file operations.
WORKDIR ${WORKSPACE_DIR}
RUN mv /agentscope_runtime/config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN mv /agentscope_runtime/config/nginx.conf.template /etc/nginx/nginx.conf.template
RUN mv /agentscope_runtime/vnc_relay.html /usr/share/novnc/vnc_relay.html
RUN git init \
    && chmod +x /agentscope_runtime/scripts/start.sh

COPY .gitignore ${WORKSPACE_DIR}

# Keep image smaller by removing build caches.
RUN pip cache purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/* \
    && npm cache clean --force \
    && rm -rf ~/.npm/_cacache

# Entrypoint:
# 1) render nginx config with SECRET_TOKEN
# 2) start supervisord, which in turn starts API + desktop + VNC stack
CMD ["/bin/sh", "-c", "envsubst '$SECRET_TOKEN' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
