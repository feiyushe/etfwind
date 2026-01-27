#!/bin/bash

cd /app
export PYTHONPATH=/app

# 启动 web 服务
uvicorn src.web.app:app --host 0.0.0.0 --port 8080
