# Operations Runbook

Deployment, monitoring, and troubleshooting guide for ETF风向标.

## Architecture Overview

```
GitHub Actions (cron: every 2 hours)
        ↓
worker_simple.py → collectors/ → realtime.py
                   (10 sources)   (Claude AI)
        ↓
    src/data/*.json
        ↓
    Upload to R2
        ↓
Cloudflare Workers (reads from R2)
```

## Deployment

### Automated (GitHub Actions)

The workflow `.github/workflows/daily_news.yml` runs:
- **Schedule**: Every 2 hours (`0 */2 * * *`)
- **Manual**: Via workflow_dispatch

Steps:
1. Checkout code
2. Setup Python 3.11
3. Install dependencies + Playwright
4. Run collection and analysis
5. Upload `latest.json` and `news.json` to R2
6. Upload `etf_master.json` (Monday only or manual trigger)

### Manual Deployment

**Workers frontend:**
```bash
cd workers && npm run deploy
```

**Data collection (local):**
```bash
PYTHONPATH=. uv run python -m src.worker_simple
```

## Required Secrets

### GitHub Actions

| Secret | Purpose |
|--------|---------|
| `CLAUDE_API_KEY` | Claude API authentication |
| `CLAUDE_BASE_URL` | API endpoint (optional) |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 access |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 secret |

### Cloudflare Workers

Configure in `workers/wrangler.toml`:
- R2 bucket binding: `invest-data`

## Monitoring

### Health Check

```bash
curl https://etf.aurora-ai.workers.dev/health
```

### Live Logs

```bash
cd workers && npm run tail
```

### Check Data Freshness

```bash
curl -s https://etf.aurora-ai.workers.dev/api/data | jq '.updated_at'
```

## Common Issues

### 1. Stale Data (not updating)

**Symptoms**: `updated_at` is hours old

**Check**:
1. GitHub Actions workflow status
2. Claude API key validity
3. R2 upload permissions

**Fix**:
- Trigger manual workflow run
- Check secrets in GitHub repo settings

### 2. Collector Failures

**Symptoms**: Low `news_count`, missing sources in `source_stats`

**Check**:
```bash
# Run locally to see errors
PYTHONPATH=. uv run python -m src.worker_simple
```

**Common causes**:
- Website structure changed
- Rate limiting
- Playwright browser issues

### 3. Workers 500 Errors

**Check**:
```bash
cd workers && npm run tail
```

**Common causes**:
- R2 binding misconfigured
- TypeScript errors
- Missing environment variables

### 4. Claude API Errors

**Symptoms**: Analysis fails, empty sectors

**Check**:
- API key validity
- Rate limits
- Model availability

**Fix**:
- Rotate API key
- Use `CLAUDE_BASE_URL` for proxy

## Rollback Procedures

### Workers Rollback

```bash
# List deployments
npx wrangler deployments list

# Rollback to previous
npx wrangler rollback
```

### Data Rollback

R2 doesn't have versioning enabled. To restore data:
1. Re-run GitHub Actions workflow
2. Or run collection locally and upload manually

## API Endpoints Reference

| Endpoint | Description |
|----------|-------------|
| `GET /` | Homepage HTML |
| `GET /news` | News list (supports `?source=` filter) |
| `GET /api/data` | Analysis JSON |
| `GET /api/funds?codes=518880` | ETF realtime quotes |
| `GET /api/batch-sector-etfs?sectors=黄金` | Batch sector ETFs |
| `GET /api/etf-master` | ETF master data |
| `GET /health` | Health check |
