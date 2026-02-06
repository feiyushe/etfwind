"""更新 ETF Master 数据（完整版）

用法：
    CLAUDE_API_KEY=xxx uv run python scripts/update_etf_master.py

功能：
    1. 从新浪获取全量 ETF 列表
    2. 爬取东方财富获取详细信息（管理人、投资范围等）
    3. AI 批量分类到板块 + 精炼描述
    4. 保存到 config/etf_master.json
"""

import asyncio
import json
import os
import re
from pathlib import Path
from datetime import datetime

import httpx
from loguru import logger

# 配置
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# 排除关键词
EXCLUDE_KEYWORDS = [
    "债", "货币", "添益", "日利", "短融",
    "500", "300", "1000", "50ETF", "科创50", "创业板ETF",
    "A500", "中证A", "综指", "红利",
    "纳指", "标普", "日经", "德国", "法国", "中韩", "中概",
    "沙特", "巴西", "越南", "印度",
    "恒生指数", "国企", "央企",
    "保证金", "自由现金", "期货", "豆粕", "能源化工",
]


def should_exclude(name: str) -> bool:
    return any(kw in name for kw in EXCLUDE_KEYWORDS)


async def fetch_all_etfs() -> list[dict]:
    """从新浪获取全量 ETF"""
    all_etfs = []
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, 15):
            resp = await client.get(
                "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData",
                params={
                    "page": page, "num": 100,
                    "sort": "amount", "asc": 0,
                    "node": "etf_hq_fund",
                },
                headers={"Referer": "https://finance.sina.com.cn"},
            )
            data = resp.json()
            if not data:
                break
            for item in data:
                all_etfs.append({
                    "code": item.get("code", ""),
                    "name": item.get("name", ""),
                    "amount": float(item.get("amount", 0)),
                })
            if len(data) < 100:
                break
    logger.info(f"获取到 {len(all_etfs)} 个 ETF")
    return all_etfs


async def fetch_etf_detail(client: httpx.AsyncClient, code: str) -> dict:
    """从东方财富爬取 ETF 详细信息"""
    try:
        url = f"https://fundf10.eastmoney.com/jbgk_{code}.html"
        resp = await client.get(url, timeout=10)
        text = resp.text

        info = {"code": code}
        # 交易所
        info["exchange"] = "上海" if code.startswith("5") else "深圳"

        # 基金全称
        m = re.search(r'基金全称</th><td[^>]*>([^<]+)', text)
        if m:
            info["full_name"] = m.group(1).strip()

        # 基金简称
        m = re.search(r'基金简称</th><td[^>]*>([^<]+)', text)
        if m:
            info["short_name"] = m.group(1).strip()

        # 基金管理人
        m = re.search(r'基金管理人</th><td[^>]*><a[^>]*>([^<]+)', text)
        if m:
            info["manager"] = m.group(1).strip()

        # 成立日期
        m = re.search(r'成立日期/规模</th><td[^>]*>(\d{4}年\d{2}月\d{2}日)', text)
        if m:
            info["establish_date"] = m.group(1).strip()

        # 投资范围
        m = re.search(r'投资范围</label>.*?<p>\s*(.+?)\s*</p>', text, re.DOTALL)
        if m:
            info["scope"] = m.group(1).strip()[:500]  # 限制长度

        # 风险收益特征
        m = re.search(r'风险收益特征</label>.*?<p>\s*(.+?)\s*</p>', text, re.DOTALL)
        if m:
            info["risk"] = m.group(1).strip()[:300]

        return info
    except Exception as e:
        logger.warning(f"获取 {code} 详情失败: {e}")
        return {"code": code}


async def ai_classify_batch(client: httpx.AsyncClient, etf_infos: list[dict]) -> dict:
    """AI 批量分类 ETF 到板块"""
    if not etf_infos or not CLAUDE_API_KEY:
        return {}

    etf_list = "\n".join([
        f"- {info['code']} {info.get('short_name','')}: {info.get('scope','')[:150]}"
        for info in etf_infos
    ])

    prompt = f"""对以下ETF进行行业板块分类并生成描述。

## ETF列表
{etf_list}

## 分类规则
1. 分类到A股行业板块：黄金、有色、芯片、半导体、人工智能、医药、证券、银行、军工、光伏、新能源、锂电池、白酒、消费、农业、煤炭、钢铁、石油、化工、电力、机器人、通信、游戏、传媒、房地产、家电、环保、汽车、软件、互联网、恒生科技、港股
2. 无法分类的标记为"其他"

## 描述要求
- 20-30字，突出投资标的和特点
- 不要重复ETF名称
- 示例：
  - 黄金ETF → "跟踪上海金现货，对冲通胀和避险首选"
  - 芯片ETF → "覆盖半导体设计、制造、封测全产业链龙头"
  - 证券ETF → "券商股打包投资，牛市弹性大"

## 输出JSON
```json
{{
  "ETF代码": {{"sector": "板块", "desc": "描述"}},
  ...
}}
```"""

    try:
        resp = await client.post(
            f"{CLAUDE_BASE_URL.rstrip('/')}/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=120,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)
    except Exception as e:
        logger.warning(f"AI分类失败: {e}")
        return {}


async def fetch_kline_changes(client: httpx.AsyncClient, code: str) -> dict:
    """获取 ETF 的 90 天 K 线数据和 5日/20日涨跌幅"""
    secid = f"1.{code}" if code.startswith("5") else f"0.{code}"
    try:
        resp = await client.get(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params={
                "secid": secid,
                "fields1": "f1,f2,f3",
                "fields2": "f51,f52,f53,f54,f55,f56",
                "klt": "101",
                "fqt": "1",
                "end": "20500101",
                "lmt": "95",
            },
        )
        klines = resp.json().get("data", {}).get("klines", [])
        if not klines:
            return {}

        closes = [float(k.split(",")[2]) for k in klines]
        today_close = closes[-1]
        change_5d = 0
        change_20d = 0

        if len(closes) >= 6:
            change_5d = round((today_close - closes[-6]) / closes[-6] * 100, 2)
        if len(closes) >= 21:
            change_20d = round((today_close - closes[-21]) / closes[-21] * 100, 2)

        kline_data = closes[-90:] if len(closes) >= 90 else closes
        return {
            "change_5d": change_5d,
            "change_20d": change_20d,
            "kline": kline_data,
        }
    except Exception as e:
        logger.warning(f"获取K线失败 {code}: {e}")
        return {}


async def main():
    """主函数"""
    if not CLAUDE_API_KEY:
        logger.error("请设置 CLAUDE_API_KEY 环境变量")
        return

    # Step 1: 获取全量 ETF
    logger.info("=== Step 1: 获取 ETF 列表 ===")
    all_etfs = await fetch_all_etfs()

    # 筛选活跃 ETF
    active_etfs = [
        e for e in all_etfs
        if e["amount"] > 5e6 and not should_exclude(e["name"])
    ]
    logger.info(f"筛选后: {len(active_etfs)} 个活跃行业ETF")

    # Step 2: 爬取详细信息
    logger.info("=== Step 2: 获取 ETF 详情 ===")
    details = []
    async with httpx.AsyncClient(timeout=30) as client:
        sem = asyncio.Semaphore(5)

        async def fetch_with_sem(etf):
            async with sem:
                detail = await fetch_etf_detail(client, etf["code"])
                detail["name"] = etf["name"]
                detail["amount_yi"] = round(etf["amount"] / 1e8, 2)
                return detail

        tasks = [fetch_with_sem(e) for e in active_etfs]
        details = await asyncio.gather(*tasks)
        details = [d for d in details if d.get("code")]
    logger.info(f"获取到 {len(details)} 个 ETF 详情")

    # Step 3: AI 批量分类
    logger.info("=== Step 3: AI 分类 ===")
    all_classifications = {}
    async with httpx.AsyncClient(timeout=120) as client:
        for i in range(0, len(details), 30):
            batch = details[i:i+30]
            logger.info(f"处理 {i+1}-{i+len(batch)}/{len(details)}...")
            result = await ai_classify_batch(client, batch)
            all_classifications.update(result)
            await asyncio.sleep(1)  # 避免限流

    # Step 4: 获取 K 线数据
    logger.info("=== Step 4: 获取 K 线数据 ===")
    kline_map = {}
    async with httpx.AsyncClient(timeout=30, headers={"Referer": "https://quote.eastmoney.com/"}) as client:
        sem = asyncio.Semaphore(5)

        async def fetch_kline_with_sem(code):
            async with sem:
                return code, await fetch_kline_changes(client, code)

        codes = [d["code"] for d in details]
        tasks = [fetch_kline_with_sem(c) for c in codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, tuple):
                code, data = r
                if data:
                    kline_map[code] = data
    logger.info(f"获取到 {len(kline_map)}/{len(details)} 个 ETF 的 K 线数据")

    # Step 5: 构建最终数据
    logger.info("=== Step 5: 构建数据 ===")
    etf_master = {}
    sector_map = {}

    for detail in details:
        code = detail["code"]
        classify = all_classifications.get(code, {})
        sector = classify.get("sector", "其他")
        desc = classify.get("desc", "")

        kline_data = kline_map.get(code, {})
        etf_master[code] = {
            "code": code,
            "name": detail.get("name", ""),
            "full_name": detail.get("full_name", ""),
            "exchange": detail.get("exchange", ""),
            "manager": detail.get("manager", ""),
            "establish_date": detail.get("establish_date", ""),
            "amount_yi": detail.get("amount_yi", 0),
            "sector": sector,
            "desc": desc,
            "scope": detail.get("scope", "")[:200],
            "risk": detail.get("risk", "")[:100],
            "change_5d": kline_data.get("change_5d", 0),
            "change_20d": kline_data.get("change_20d", 0),
            "kline": kline_data.get("kline", []),
        }

        # 构建板块索引
        if sector != "其他":
            if sector not in sector_map:
                sector_map[sector] = []
            sector_map[sector].append(code)

    # 每个板块按成交额排序
    for sector in sector_map:
        sector_map[sector].sort(
            key=lambda c: etf_master[c]["amount_yi"],
            reverse=True
        )

    # 保存结果
    output = {
        "etfs": etf_master,
        "sectors": sector_map,
        "sector_list": sorted(sector_map.keys()),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    output_file = Path(__file__).parent.parent / "config" / "etf_master.json"
    output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))

    # 统计
    logger.info(f"\n=== 完成 ===")
    logger.info(f"共 {len(etf_master)} 个 ETF，{len(sector_map)} 个板块")
    for sector in sorted(sector_map.keys()):
        codes = sector_map[sector]
        logger.info(f"  {sector}: {len(codes)} 个")
    logger.info(f"\n已保存到 {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
