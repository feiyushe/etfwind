"""简化版 Worker - 采集+分析，结果存JSON文件"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter
from loguru import logger

from src.config import settings
from src.collectors import NewsAggregator
from src.analyzers.realtime import analyze
from src.services.fund_service import fund_service

# 输出目录 - 放到 src/web/data 避免被 volume 覆盖
DATA_DIR = Path(__file__).parent / "web" / "data"
DATA_DIR.mkdir(exist_ok=True)


async def run():
    """运行采集和分析"""
    logger.info("开始采集新闻...")

    # 采集
    agg = NewsAggregator(include_international=True, include_playwright=True)
    try:
        news = await agg.collect_all()
        source_stats = dict(Counter(item.source for item in news.items))
        logger.info(f"采集到 {len(news.items)} 条新闻: {source_stats}")
    finally:
        await agg.close()

    # AI 分析
    logger.info("开始 AI 分析...")
    result = await analyze(news.items)

    # 保存结果
    beijing_tz = timezone(timedelta(hours=8))
    output = {
        "result": result,
        "updated_at": datetime.now(beijing_tz).isoformat(),
        "news_count": len(news.items),
        "source_stats": source_stats,
    }

    output_file = DATA_DIR / "latest.json"
    output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    logger.info(f"结果已保存到 {output_file}")

    # 抓取基金数据
    await fetch_fund_data(result)

    # 生成 ETF 板块映射
    await fetch_etf_map()

    return output


async def fetch_fund_data(result: dict):
    """根据分析结果中的板块，动态获取相关ETF数据"""
    sectors = result.get("sectors", [])
    if not sectors:
        logger.info("没有板块数据")
        return

    # 获取板块映射
    sector_map = await fund_service.get_sector_etf_map()
    if not sector_map:
        logger.warning("无法获取板块映射")
        return

    # 收集所有相关板块的ETF代码
    codes = set()
    for sector in sectors:
        sector_name = sector.get("name", "")
        for key, etfs in sector_map.items():
            if key in sector_name or sector_name in key:
                for code, name in etfs[:3]:  # 每个板块取前3个
                    codes.add(code)
                break

    if not codes:
        logger.info("没有匹配到ETF代码")
        return

    logger.info(f"抓取 {len(codes)} 个基金数据: {codes}")

    try:
        fund_data = await fund_service.batch_get_funds(list(codes))

        # 保存基金数据
        funds_file = DATA_DIR / "funds.json"
        beijing_tz = timezone(timedelta(hours=8))
        output = {
            "funds": fund_data,
            "updated_at": datetime.now(beijing_tz).isoformat(),
        }
        funds_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))
        logger.info(f"基金数据已保存到 {funds_file}")
    except Exception as e:
        logger.warning(f"抓取基金数据失败: {e}")


async def fetch_etf_map():
    """生成 ETF 板块映射文件"""
    logger.info("生成 ETF 板块映射...")

    try:
        # 强制刷新缓存
        fund_service._etf_cache_time = 0
        sector_map = await fund_service.get_sector_etf_map()

        # 保存映射
        etf_map_file = DATA_DIR / "etf_map.json"
        beijing_tz = timezone(timedelta(hours=8))
        output = {
            "sectors": sector_map,
            "updated_at": datetime.now(beijing_tz).isoformat(),
        }
        etf_map_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))
        logger.info(f"ETF 映射已保存到 {etf_map_file}，共 {len(sector_map)} 个板块")
    except Exception as e:
        logger.warning(f"生成 ETF 映射失败: {e}")


if __name__ == "__main__":
    asyncio.run(run())
