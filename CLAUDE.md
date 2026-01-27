# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

基金推荐助手 - 自动采集财经新闻，通过 Claude AI 分析生成投资建议和基金推荐，部署在 Fly.io。

## Commands

```bash
# 启动 Web 服务（本地开发）
uv run uvicorn src.web.app:app --reload --port 8000

# 手动触发分析（本地）
PYTHONPATH=. uv run python -c "
import asyncio
from src.analyzers import IncrementalAnalyzer
from src.web.database import init_db, get_today_news
async def main():
    await init_db()
    news = await get_today_news()
    analyzer = IncrementalAnalyzer()
    await analyzer.analyze_new_news([n['id'] for n in news[:30]], force_full=True)
asyncio.run(main())
"

# 部署到 Fly.io
fly deploy

# 查看生产日志
fly logs --app invest-report --no-tail | tail -50
```

## Architecture

```
GitHub Actions (定时触发 + 运行采集/分析)
        ↓
collectors/  →  IncrementalAnalyzer  →  Supabase  ←  FastAPI (Fly.io)
(6个采集器)      (Claude API)           (PostgreSQL)   (仅展示)
```

**核心流程：**
1. GitHub Actions 工作日每小时运行采集和分析
2. `NewsAggregator` 并发调用6个采集器
3. 新闻去重后存入 Supabase `news_items` 表
4. 当新增新闻 ≥5 条且距上次更新 ≥30分钟时，触发 `IncrementalAnalyzer`
5. AI 分析结果存入 `daily_reports` 表
6. Fly.io 仅运行 Web 服务，从 Supabase 读取数据展示

**关键模块：**
- `src/worker.py`: 采集+分析逻辑（由 GitHub Actions 触发）
- `src/analyzers/incremental_analyzer.py`: 增量分析器，调用 Claude API
- `src/analyzers/prompts.py`: AI 分析 Prompt 模板
- `src/web/database.py`: Supabase 数据库操作
- `src/web/app.py`: FastAPI 应用，含 SSE 实时推送

**采集器（src/collectors/）：**
- 国内：CLSNewsCollector、EastMoneyCollector、SinaFinanceCollector
- 国际：CNBCCollector、BloombergCollector、WSJCollector（RSS）

## Configuration

环境变量（.env）：
- `CLAUDE_API_KEY`: Claude API 密钥（必需）
- `CLAUDE_BASE_URL`: API 地址，支持中转
- `CLAUDE_MODEL`: 模型名称，默认 claude-opus-4-5-20251101
- `SUPABASE_URL`: Supabase 项目 URL（必需）
- `SUPABASE_KEY`: Supabase anon key（必需）

## Deployment

- **Web**: Fly.io（新加坡，256MB，auto_stop）
- **采集/分析**: GitHub Actions（工作日 08:00-20:00 每小时）
- **数据库**: Supabase（PostgreSQL）
- **URL**: https://invest-report.fly.dev/

## Key Data Structures

**daily_reports 表核心字段：**
- `focus_events`: 焦点事件数组，每个事件包含 title、analysis、suggestion、related_funds、sources
- `market_emotion`: 市场情绪指数（0-100）
- `position_advices`: 仓位建议（股票/债券/货币/黄金）

**focus_events 中的 related_funds 格式：**
```json
[{"code": "518880", "name": "黄金ETF", "reason": "跟踪金价，流动性好"}]
```

## Timezone Handling

- 数据库存储 UTC 时间
- `get_daily_report()` 返回北京时间（用于展示）
- `get_daily_report_raw()` 返回原始 UTC 时间（用于内部计算）

## Tech Stack

**后端框架：** Python 3.11+ / FastAPI / Uvicorn / Jinja2

**AI & 数据：** Anthropic SDK (Claude API) / Pydantic / httpx

**数据库：** Supabase (PostgreSQL)

**工具：** Loguru (日志) / aiosmtplib (邮件)

**部署：** Fly.io / GitHub Actions / uv (包管理)

**特点：** 全异步架构、增量分析、SSE 实时推送、多源并发采集
