@echo off
chcp 65001 >nul
REM ============================================================
REM  AIOps 平台一键启动（含 DeepSeek 大脑）
REM  只改下面一行：把 sk- 开头你的 key 粘贴进去，保存后双击本文件
REM ============================================================
cd /d D:\aiops-roadmap\backend

REM ===== 唯一需要你填的一行 =====
set LLM_API_KEY=sk-把这里替换成你的DeepSeek密钥

REM ===== 以下不用动 =====
set LLM_BASE_URL=https://api.deepseek.com/v1
set LLM_MODEL=deepseek-chat
REM 接你本机 RAGFlow 时再取消下面三行注释并填值：
REM set RAGFLOW_BASE_URL=http://127.0.0.1:9380
REM set RAGFLOW_API_KEY=ragflow-xxxxxxxx
REM set RAGFLOW_DATASET_IDS=你的dataset id

echo [AIOps] backend: http://localhost:8600/dashboard
echo [AIOps] LLM brain: %LLM_BASE_URL% model=%LLM_MODEL%
D:\python3.11\python.exe -m uvicorn app.server:app --port 8600 --host 0.0.0.0
pause
