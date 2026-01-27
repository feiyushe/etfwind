"""重建报告脚本：清理历史数据，重新爬取最近7天新闻并生成分析"""

import asyncio
from datetime import date, timedelta

from loguru import logger
from supabase import create_client

from src.config import settings
from src.collectors import NewsAggregator
from src.analyzers import IncrementalAnalyzer


def get_supabase():
    """获取 Supabase 客户端"""
    return create_client(settings.supabase_url, settings.supabase_key)


async def clear_all_data():
    """清理所有历史数据"""
    logger.info("开始清理历史数据...")
    sb = get_supabase()

    # 清理 daily_reports
    try:
        sb.table("daily_reports").delete().neq("id", 0).execute()
        logger.info("已清理 daily_reports 表")
    except Exception as e:
        logger.warning(f"清理 daily_reports 失败: {e}")

    # 清理 news_items
    try:
        sb.table("news_items").delete().neq("id", 0).execute()
        logger.info("已清理 news_items 表")
    except Exception as e:
        logger.warning(f"清理 news_items 失败: {e}")

    # 清理 market_summaries
    try:
        sb.table("market_summaries").delete().neq("id", 0).execute()
        logger.info("已清理 market_summaries 表")
    except Exception as e:
        logger.warning(f"清理 market_summaries 失败: {e}")

    logger.info("历史数据清理完成")


async def collect_news():
    """采集新闻"""
    logger.info("开始采集新闻...")
    aggregator = NewsAggregator(include_international=True)

    try:
        collection = await aggregator.collect_all()
        logger.info(f"采集到 {len(collection.items)} 条新闻")
        return collection.items
    finally:
        await aggregator.close()


async def store_news(news_items) -> list[int]:
    """存储新闻到数据库"""
    import hashlib

    logger.info(f"开始存储 {len(news_items)} 条新闻...")
    sb = get_supabase()
    new_ids = []

    for item in news_items:
        # 计算内容哈希
        text = f"{item.title}:{item.content[:200] if item.content else ''}"
        content_hash = hashlib.md5(text.encode()).hexdigest()

        # 检查是否已存在
        existing = sb.table("news_items").select("id").eq(
            "content_hash", content_hash
        ).execute()

        if existing.data:
            continue

        data = {
            "title": item.title,
            "content": item.content or "",
            "source": item.source,
            "source_type": item.source_type.value if hasattr(item.source_type, 'value') else str(item.source_type),
            "url": item.url,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "content_hash": content_hash,
            "language": item.language,
            "summary_zh": item.summary_zh,
        }

        try:
            result = sb.table("news_items").insert(data).execute()
            if result.data:
                new_ids.append(result.data[0]["id"])
        except Exception as e:
            logger.warning(f"存储新闻失败: {e}")

    logger.info(f"成功存储 {len(new_ids)} 条新闻")
    return new_ids


async def generate_report_for_date(target_date: date, news_ids: list[int]):
    """为指定日期生成报告"""
    logger.info(f"为 {target_date} 生成报告...")

    analyzer = IncrementalAnalyzer()

    # 强制全量分析
    result = await analyzer.analyze_new_news(news_ids, force_full=True)

    # 更新报告日期
    sb = get_supabase()
    sb.table("daily_reports").update({
        "report_date": target_date.isoformat()
    }).eq("report_date", date.today().isoformat()).execute()

    logger.info(f"{target_date} 报告生成完成")
    return result


async def generate_today_report(news_ids: list[int]):
    """生成今日报告"""
    logger.info("生成今日报告...")

    analyzer = IncrementalAnalyzer()
    result = await analyzer.analyze_new_news(news_ids, force_full=True)

    logger.info("今日报告生成完成")
    return result


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始重建报告流程")
    logger.info("=" * 50)

    # 1. 清理历史数据
    await clear_all_data()

    # 2. 采集新闻
    news_items = await collect_news()

    if not news_items:
        logger.error("没有采集到新闻，退出")
        return

    # 3. 存储新闻
    news_ids = await store_news(news_items)

    if not news_ids:
        logger.error("没有新闻存储成功，退出")
        return

    # 4. 生成今日报告
    await generate_today_report(news_ids)

    logger.info("=" * 50)
    logger.info("重建报告流程完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
