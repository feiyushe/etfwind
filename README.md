# 投资分析报告系统

每日财经新闻收集与基金投资建议系统。

## 部署到 Railway

1. Fork 或 Push 代码到 GitHub
2. 访问 [railway.app](https://railway.app)
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择此仓库
5. 添加环境变量（Settings → Variables）:
   - `CLAUDE_API_KEY`
   - `CLAUDE_BASE_URL`
   - `CLAUDE_MODEL`
6. 部署完成后会自动生成域名

## 本地运行

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run_web.py
```
