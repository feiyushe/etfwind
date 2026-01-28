# ETF风向标

AI 驱动的 ETF 投资风向分析工具。自动采集财经新闻，通过 Claude AI 分析生成板块研判和 ETF 推荐。

**在线访问**: https://etf.aurora-ai.workers.dev/

## 功能特点

- 自动采集 10+ 财经新闻源（财联社、东方财富、新浪、Bloomberg、CNBC 等）
- Claude AI 分析市场动态，生成板块研判
- 智能匹配板块相关 ETF，展示实时行情
- 每小时自动更新

## 架构

```
GitHub Actions (每小时)
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

## 技术亮点

### 多源采集 + 智能去重

采集器基类 + 策略模式，10个采集器并发执行：
- httpx 采集器：财联社、东方财富、新浪、Bloomberg、CNBC
- Playwright 采集器：动态渲染页面（金十、华尔街见闻）
- 按标题去重，按时间排序，处理混合时区

### AI 语义分类 ETF

Claude AI 批量分类 ETF 到行业板块：
- 语义理解："科创芯片ETF" 和 "半导体龙头" 都归入"芯片"
- 统一命名：券商→证券，医疗→医药，贵金属→黄金
- 自动排除宽基指数、债券、货币、跨境 ETF

### 多级数据源降级

主源失败自动切换备用源：
- ETF列表：新浪 API → 东方财富 API
- K线数据：东方财富 → 新浪
- 缓存机制减少 API 调用

### SSR + 异步水合

- 服务端预渲染历史数据（20日涨跌、K线图）
- 客户端异步加载实时价格，首屏秒开

### Serverless 零成本

- GitHub Actions 免费运行采集
- Cloudflare Workers 免费托管
- R2 存储静态 JSON，无数据库
