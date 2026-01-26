#!/bin/bash

cd /app
export PYTHONPATH=/app

# 启动 worker 后台进程（使用模块方式运行）
python -m src.worker &

# 启动 web 服务（前台）
uvicorn src.web.app:app --host 0.0.0.0 --port 8080
