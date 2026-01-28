# Contributing Guide

Development workflow and setup for ETF风向标.

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Cloudflare account (for Workers deployment)

## Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/lichengzhe/etfwind.git
cd etfwind
```

2. Create `.env` file from template:
```bash
cp .env.example .env
```

3. Configure environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `CLAUDE_API_KEY` | Yes | Claude API key (sk-xxx format) |
| `CLAUDE_BASE_URL` | No | API endpoint, defaults to `https://api.anthropic.com` |
| `CLAUDE_MODEL` | No | Model name, defaults to `claude-sonnet-4-20250514` |
| `WECOM_WEBHOOK_URL` | No | WeCom robot webhook for notifications |
| `SMTP_HOST` | No | SMTP server for email alerts |
| `SMTP_PORT` | No | SMTP port (default 465) |
| `SMTP_USER` | No | SMTP username |
| `SMTP_PASSWORD` | No | SMTP password |
| `EMAIL_RECIPIENTS` | No | Comma-separated email recipients |

4. Install Python dependencies:
```bash
pip install -e .
# Or with uv
uv pip install -e .
```

5. Install Playwright browsers (for news collection):
```bash
python -m playwright install chromium --with-deps
```

6. Install Workers dependencies:
```bash
cd workers && npm install
```

## Available Scripts

### Python (Root Directory)

| Command | Description |
|---------|-------------|
| `PYTHONPATH=. uv run python -m src.worker_simple` | Run news collection + AI analysis |

### Workers (workers/ Directory)

| Command | Description |
|---------|-------------|
| `npm run dev` | Start local development server (wrangler dev) |
| `npm run deploy` | Deploy to Cloudflare Workers |
| `npm run tail` | Stream live logs from Workers |
| `npm run typecheck` | Run TypeScript type checking |

## Development Workflow

### 1. Local Development

```bash
# Terminal 1: Run collection + analysis (generates src/data/*.json)
PYTHONPATH=. uv run python -m src.worker_simple

# Terminal 2: Start Workers dev server
cd workers && npm run dev
```

The dev server runs at `http://localhost:8787`.

### 2. Making Changes

- **Collectors**: `src/collectors/` - Add or modify news sources
- **AI Analysis**: `src/analyzers/realtime.py` - Modify Claude prompts
- **Frontend**: `workers/src/` - Hono routes and page templates
- **ETF Data**: `src/services/fund_service.py` - ETF data fetching

### 3. Testing Changes

After modifying frontend code:
1. Deploy: `cd workers && npm run deploy`
2. Verify at https://etf.aurora-ai.workers.dev/

### 4. Code Style

- Python: Follow PEP 8
- TypeScript: Use strict mode, run `npm run typecheck`
- No emojis in code unless explicitly requested

## Project Structure

```
invest/
├── src/
│   ├── collectors/      # 10 news collectors
│   ├── analyzers/       # Claude AI analysis
│   ├── services/        # ETF data services
│   ├── data/            # Generated JSON output
│   └── worker_simple.py # Main entry point
├── workers/
│   ├── src/
│   │   ├── index.ts     # Hono routes
│   │   ├── pages/       # HTML templates
│   │   └── services/    # API services
│   └── wrangler.toml    # Cloudflare config
└── .github/workflows/   # GitHub Actions
```

## Dependencies

### Python (pyproject.toml)

| Package | Purpose |
|---------|---------|
| httpx | HTTP client for API calls |
| anthropic | Claude API SDK |
| pydantic | Data validation |
| loguru | Logging |
| beautifulsoup4 | HTML parsing |
| playwright | Browser automation |

### Workers (package.json)

| Package | Purpose |
|---------|---------|
| hono | Web framework |
| wrangler | Cloudflare CLI |
| typescript | Type checking |
