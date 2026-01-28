# ETF风向标

AI 驱动的 ETF 投资风向分析工具。自动采集财经新闻，通过 Claude AI 分析生成板块研判和 ETF 推荐。

**在线访问**: https://etf.aurora-ai.workers.dev/

## 功能特点

- 自动采集 10+ 财经新闻源（财联社、东方财富、新浪、Bloomberg、CNBC 等）
- Claude AI 分析市场动态，生成板块研判
- 智能匹配板块相关 ETF，展示实时行情
- 每 30 分钟自动更新

## 架构

```
GitHub Actions (每30分钟)
        ↓
采集器 → Claude AI 分析 → JSON 数据
        ↓
    上传到 Cloudflare R2
        ↓
Cloudflare Workers 渲染页面
```

## 本地开发

```bash
# 安装依赖
pip install -e .

# 运行采集+分析
PYTHONPATH=. uv run python -m src.worker_simple

# Workers 本地开发
cd workers && npm run dev

# 部署 Workers
cd workers && npm run deploy
```

## 环境变量

- `CLAUDE_API_KEY`: Claude API 密钥
- `CLAUDE_BASE_URL`: API 地址（可选，支持中转）
- `CLAUDE_MODEL`: 模型名称（默认 claude-sonnet-4-20250514）

## 技术栈

- **前端**: Cloudflare Workers + Hono + TypeScript
- **AI**: Claude API
- **数据源**: 东方财富 API
- **采集**: httpx + BeautifulSoup + Playwright
- **部署**: GitHub Actions + Cloudflare R2
