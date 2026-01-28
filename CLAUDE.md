# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ETF风向标 - AI 驱动的 ETF 投资风向分析工具。自动采集财经新闻，通过 Claude AI 分析生成板块研判和 ETF 推荐，部署在 Cloudflare Workers。

**在线访问**: https://etf.aurora-ai.workers.dev/
**GitHub**: https://github.com/lichengzhe/etfwind

## Commands

```bash
# 手动运行采集+分析（输出到 src/data/）
PYTHONPATH=. uv run python -m src.worker_simple

# 部署 Workers 前端
cd workers && npx wrangler deploy

# 本地开发 Workers
cd workers && npx wrangler dev
```

## Architecture

```
GitHub Actions (每2小时)
        ↓
worker_simple.py → collectors/ → realtime.py → src/data/*.json
                   (10个采集器)   (Claude API)        ↓
                                              上传到 R2
                                                   ↓
                                            Cloudflare Workers
                                            从 R2 读取 JSON
```

**关键文件：**
- `src/worker_simple.py` - 采集+分析入口
- `src/analyzers/realtime.py` - Claude AI 分析
- `src/collectors/` - 10个新闻采集器
- `src/services/fund_service.py` - ETF 数据服务
- `workers/src/index.ts` - Hono 路由
- `workers/src/pages/Home.ts` - 首页渲染

## Configuration

环境变量（.env）：
- `CLAUDE_API_KEY`: Claude API 密钥（必需）
- `CLAUDE_BASE_URL`: API 地址，支持中转
- `CLAUDE_MODEL`: 模型名称，默认 claude-sonnet-4-20250514

Cloudflare R2（数据存储）：
- Bucket: `invest-data`
- GitHub Secrets: `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`

## Deployment

- **Web**: Cloudflare Workers（`workers/`）
- **采集/分析**: GitHub Actions（每 2 小时，含 Playwright）
- **数据存储**: Cloudflare R2（`invest-data` bucket）
- **URL**: https://etf.aurora-ai.workers.dev/

## Key Data Structures

**latest.json（AI 分析结果）：**
```json
{
  "result": {
    "market_view": "🎯 市场状态一句话",
    "narrative": "市场全景分析（150字）",
    "sectors": [
      {
        "name": "板块名",
        "heat": 5,
        "direction": "利好/利空/中性",
        "analysis": "板块深度分析（80-100字）",
        "news": ["📰 消息 → 解读"]
      }
    ],
    "risk_level": "低/中/高"
  },
  "updated_at": "2026-01-28T10:00:00+08:00",
  "news_count": 302,
  "source_stats": {"财联社": 50, "东方财富": 35, ...}
}
```

**ETF 实时数据（/api/funds）：**
```json
{
  "518880": {
    "code": "518880",
    "name": "黄金ETF",
    "price": 10.934,
    "change_pct": 0.09,
    "change_5d": 8.45,
    "change_20d": 13.31,
    "amount_yi": 83.96,
    "flow_yi": -4.25,
    "turnover": 7.06,
    "kline": [9.563, 9.363, ...]
  }
}
```

## API Endpoints

**Workers (workers/src/index.ts)：**
- `GET /` - 首页
- `GET /news` - 新闻列表
- `GET /api/data` - 分析数据 JSON
- `GET /api/funds?codes=518880,512760` - ETF 实时行情
- `GET /api/batch-sector-etfs?sectors=黄金,芯片` - 批量板块 ETF
- `GET /api/etf-master` - ETF 主数据
- `GET /health` - 健康检查

## Tech Stack

**前端：** Cloudflare Workers / Hono / TypeScript

**AI：** Claude API (httpx 直接调用)

**数据源：** 东方财富 API

**采集：** httpx / BeautifulSoup / Playwright（GitHub Actions）

**部署：** Cloudflare Workers + R2 / GitHub Actions / uv (包管理)

## Lessons Learned

### Python 命令必须用 uv run

本项目使用 uv 管理 Python 依赖，运行任何 Python 命令都必须加 `uv run` 前缀：

```bash
# 正确
uv run python -m src.worker_simple
uv run python -c "from src.config import settings; print(settings)"

# 错误（会报 ModuleNotFoundError）
python -m src.worker_simple
python3 -c "..."
```

### Playwright 闭环验证

修改前端代码后，使用 Playwright 自动打开网站验证效果：
```
1. 部署后用 browser_navigate 打开页面
2. 用 browser_snapshot 获取页面结构，检查数据是否正确渲染
3. 发现问题 → 修复代码 → 重新部署 → 再次验证
4. 完成后用 browser_close 关闭浏览器
```

**注意**：不要用 browser_take_screenshot 截图后发给自己看，图片会导致 context 溢出。始终使用 browser_snapshot 获取文本结构。

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

## AI 工作方法论

### 核心循环

**发现 → 理解 → 计划 → 执行 → 试错 → 反馈 → 修正 → 迭代 → 反思**

### 关键原则

1. **突破需要想象力**
   - 避免路径依赖，适当发散思考
   - 大方向和策略的改变比细节优化更重要
   - 工具放大改变的效果和范围（对的和错的都会放大）

2. **积极使用工具**
   - 主动使用 skill、plugin、command
   - AI 只说不做无法产生改变
   - 代码无差别，随时可以重构

3. **从错误中学习**
   - 及时反思总结，增加到 CLAUDE.md
   - 通过 demo 和 case 学习，提取抽象可复制的经验
   - 意识到环境和反馈对自己的影响

4. **最小化 vs 最积极**
   - 架构足够好时，个体智能不需要太高
   - 最小化使用 AI（简单任务）
   - 最积极使用 AI（复杂决策、创意生成）
