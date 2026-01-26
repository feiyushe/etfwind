"""回填过去一周的新闻和AI分析报告"""

import asyncio
from datetime import date, timedelta

from loguru import logger

from src.collectors import NewsAggregator
from src.analyzers import IncrementalAnalyzer
from src.web.database import init_db, store_news_batch, upsert_daily_report


async def collect_and_analyze_for_date(target_date: date) -> bool:
    """为指定日期采集新闻并生成分析"""
    logger.info(f"开始处理 {target_date}")

    # 采集当前新闻（RSS只能获取最新的，无法获取历史）
    aggregator = NewsAggregator(include_international=True)
    try:
        collection = await aggregator.collect_all()
        logger.info(f"采集到 {collection.count} 条新闻")

        if collection.count == 0:
            logger.warning("未采集到新闻")
            return False

        # 存储新闻
        news_dicts = []
        for item in collection.items:
            news_dicts.append({
                "title": item.title,
                "content": item.content,
                "source": item.source,
                "source_type": item.source_type.value if hasattr(item.source_type, 'value') else str(item.source_type),
                "url": item.url,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "language": item.language,
                "summary_zh": item.summary_zh,
            })

        new_ids = await store_news_batch(news_dicts)
        logger.info(f"存储了 {len(new_ids)} 条新新闻")

        # 生成分析报告
        if new_ids:
            analyzer = IncrementalAnalyzer()
            result = await analyzer.analyze_new_news(new_ids, force_full=True)
            # 覆盖日期为目标日期
            result["report_date"] = target_date.isoformat()
            await upsert_daily_report(result)
            logger.info(f"{target_date} 报告生成完成")
            return True

        return False
    finally:
        await aggregator.close()


async def backfill_today():
    """只回填今天的数据"""
    await init_db()
    today = date.today()
    await collect_and_analyze_for_date(today)


async def main():
    """主函数：回填过去7天"""
    await init_db()

    today = date.today()
    logger.info(f"开始回填，今天是 {today}")

    # 由于RSS只能获取最新新闻，我们只能为今天生成报告
    # 历史数据需要从其他来源获取
    success = await collect_and_analyze_for_date(today)

    if success:
        logger.info("回填完成！")
    else:
        logger.warning("回填失败")


if __name__ == "__main__":
    asyncio.run(main())
