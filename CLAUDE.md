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
1. GitHub Actions 每 30 分钟运行采集和分析
2. `NewsAggregator` 并发调用6个采集器
3. 新闻去重后存入 Supabase `news_items` 表
4. 当新增新闻 ≥1 条且距上次更新 ≥5分钟时，触发 `IncrementalAnalyzer`
5. AI 分析结果存入 `daily_reports` 表，焦点事件同步存入 `focus_events` 表
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
- **采集/分析**: GitHub Actions（每 30 分钟）
- **数据库**: Supabase（PostgreSQL）
- **URL**: https://invest-report.fly.dev/

## Key Data Structures

**daily_reports 表核心字段：**
- `focus_events`: 焦点事件数组，每个事件包含 title、analysis、suggestion、related_funds、sources
- `market_emotion`: 市场情绪指数（0-100）
- `market_narrative`: 市场全景描述（2-3句话）

**focus_events 表（瀑布流独立存储）：**
- `event_hash`: 标题 MD5 哈希，用于去重
- `title`, `sector`, `analysis`, `suggestion`
- `related_funds`: 字符串数组，如 `["易方达沪深300医药ETF(512010)"]`
- `sources`: 来源数组
- `created_at`: 事件首次出现时间（瀑布流按此排序）

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

## Lessons Learned

### Playwright 闭环验证

修改前端代码后，使用 Playwright 自动打开网站验证效果：
```
1. 部署后用 browser_navigate 打开页面
2. 用 browser_snapshot 获取页面结构，检查数据是否正确渲染
3. 发现问题 → 修复代码 → 重新部署 → 再次验证
4. 完成后用 browser_close 关闭浏览器
```

### AI 结构化使用原则

让 AI 只负责"内容生成"，代码负责"结构组装"，避免让 AI 自由发挥格式：

**问题**：让 AI 直接输出完整 JSON，会导致字段遗漏、格式不一致（如 sources 有时有有时无）

**解决方案**：
1. **分步提取**：将复杂任务拆分为多个简单问题，每次只问一个方面
2. **代码组装**：由代码构建最终数据结构，AI 只填充内容
3. **明确约束**：给 AI 提供输入数据的索引，让它引用而非重新格式化
4. **验证兜底**：代码层面检查必填字段，缺失时记录警告或使用默认值

**示例**：
```python
# 不好：让 AI 输出完整 JSON
prompt = "分析新闻，输出 JSON 格式的 focus_events..."

# 好：分步提取，代码组装
step1 = "从以下新闻中识别最重要的5个事件，只输出事件标题列表"
step2 = "对于事件'{title}'，提供：1.所属板块 2.分析(80字) 3.建议(15字)"
step3 = "事件'{title}'相关的ETF代码是？从候选列表中选择：{etf_list}"
# 代码负责组装最终结构，并从原始新闻中提取 sources
```
