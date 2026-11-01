# AIOps 研判后端 —— 独立部署（与前端镜像解耦）
#
# 复盘修正：此前仓库只有构建静态前端的 Dockerfile，后端"部署路径"不存在。
# 现在后端可独立容器化：
#   docker build -f backend/Dockerfile -t aiops-backend ./backend
#   docker run -p 8600:8600 \
#     -e LLM_BASE_URL=https://api.deepseek.com/v1 \
#     -e LLM_API_KEY=sk-xxx \
#     -e LLM_MODEL=deepseek-chat \
#     -e AIOPS_CORS_ORIGINS=https://your-ops-site.example.com \
#     -v aiops-data:/data \
#     aiops-backend
#
# 数据（research.db / ingest.db / audit.db）落在 /data——SQLite 单文件，
# 挂卷即持久化；/data 也是容器内的工作目录（相对路径数据库都落在那里）。
FROM python:3.12-slim

WORKDIR /app

# 先拷依赖清单利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# 数据目录（挂卷点）
ENV AIOPS_DATA_DIR=/data
RUN mkdir -p /data

# 兼容：数据库相对路径统一落 /data（在 app 目录下启动时 cwd=/data 由 ENTRYPOINT 处理）
WORKDIR /data

EXPOSE 8600

# 默认规则大脑（不配 LLM 也能跑：playbook 匹配 + 排查链 + 处置分级）
ENV AIOPS_AUTO_RESEARCH=1

# --host 0.0.0.0：容器外/前端要够得到（本地裸跑同理，必须绑 0.0.0.0）
CMD ["sh", "-c", "cd /app && python -m uvicorn app.server:app --host 0.0.0.0 --port 8600"]
