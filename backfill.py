"""回溯历史新闻并生成报告"""

import asyncio
import sys
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict

import httpx
from loguru import logger

logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}", level="INFO")


async def fetch_history_news(pages: int = 80):
    """获取东方财富历史新闻"""
    all_news = []
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, pages + 1):
            url = f"https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_100_{page}_.html"
            try:
                resp = await client.get(url)
                match = re.search(r"var ajaxResult=(\{.*\})", resp.text)
                if match:
                    data = json.loads(match.group(1))
                    for item in data.get("LivesList", []):
                        all_news.append({
                            "title": item.get("title", ""),
                            "content": item.get("digest", ""),
                            "source": "东方财富",
                            "url": item.get("url_w"),
                            "time": item.get("showtime"),
                        })
                if page % 10 == 0:
                    logger.info(f"已获取 {page} 页，共 {len(all_news)} 条")
            except Exception as e:
                logger.error(f"第{page}页失败: {e}")
            await asyncio.sleep(0.2)
    return all_news


def group_by_date(news_list):
    """按日期分组新闻"""
    grouped = defaultdict(list)
    for item in news_list:
        if item.get("time"):
            date = item["time"][:10]
            grouped[date].append(item)
    return grouped


async def analyze_news(news_list, date_str, period):
    """调用 AI 分析新闻"""
    from src.config import settings
    from src.analyzers.prompts import INVESTMENT_ANALYSIS_PROMPT

    # 格式化新闻
    lines = []
    for i, item in enumerate(news_list[:30], 1):
        lines.append(f"{i}. {item['title']}")
        if item.get("content"):
            lines.append(f"   {item['content'][:150]}")
    news_content = "\n".join(lines)

    if not news_content.strip():
        logger.warning(f"{date_str} {period} 无新闻内容")
        return None

    prompt = INVESTMENT_ANALYSIS_PROMPT.format(news_content=news_content)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.claude_base_url.rstrip('/')}/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": settings.claude_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": settings.claude_model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()

    content = data["content"][0]["text"]
    return parse_ai_response(content, news_list, date_str, period)


def parse_ai_response(content, news_list, date_str, period):
    """解析 AI 响应"""
    json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = content

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        return None

    # 构建报告数据
    overview = data.get("market_overview", {})
    return {
        "period": period,
        "date_str": date_str,
        "summary": overview.get("summary", ""),
        "key_events": overview.get("key_events", []),
        "risk_factors": overview.get("risk_factors", []),
        "sector_analyses": data.get("sector_analyses", []),
        "fund_advices": data.get("fund_advices", []),
        "news_sources": news_list[:20],
    }


async def save_report_to_db(report_data):
    """保存报告到数据库"""
    import aiosqlite
    from pathlib import Path

    db_path = Path("data/reports.db")
    db_path.parent.mkdir(exist_ok=True)

    # 构建 generated_at 时间
    date_str = report_data["date_str"]
    period = report_data["period"]
    hour = "08:00:00" if period == "morning" else "18:00:00"
    generated_at = f"{date_str} {hour}"

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """INSERT INTO reports
               (period, generated_at, summary, key_events, risk_factors, sector_analyses, fund_advices, news_sources)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                period,
                generated_at,
                report_data["summary"],
                json.dumps(report_data["key_events"], ensure_ascii=False),
                json.dumps(report_data["risk_factors"], ensure_ascii=False),
                json.dumps(report_data["sector_analyses"], ensure_ascii=False),
                json.dumps(report_data["fund_advices"], ensure_ascii=False),
                json.dumps(report_data["news_sources"], ensure_ascii=False),
            ),
        )
        await db.commit()
        logger.info(f"已保存 {date_str} {period} 报告")


def split_by_period(news_list):
    """按早盘/晚盘分割新闻"""
    morning = []
    evening = []
    for item in news_list:
        time_str = item.get("time", "")
        if len(time_str) >= 16:
            hour = int(time_str[11:13])
            if hour < 12:
                morning.append(item)
            else:
                evening.append(item)
    return morning, evening


async def main():
    """主函数"""
    from src.web.database import init_db

    logger.info("开始回溯历史新闻...")

    # 初始化数据库
    await init_db()

    # 获取历史新闻 (80页约8000条，覆盖10天)
    all_news = await fetch_history_news(pages=80)
    logger.info(f"共获取 {len(all_news)} 条新闻")

    # 按日期分组
    grouped = group_by_date(all_news)
    dates = sorted(grouped.keys(), reverse=True)[:10]
    logger.info(f"将处理以下日期: {dates}")

    # 处理每一天
    for date_str in dates:
        news_of_day = grouped[date_str]
        morning_news, evening_news = split_by_period(news_of_day)

        logger.info(f"{date_str}: 早盘 {len(morning_news)} 条, 晚盘 {len(evening_news)} 条")

        # 生成早盘报告
        if morning_news:
            try:
                report = await analyze_news(morning_news, date_str, "morning")
                if report:
                    await save_report_to_db(report)
            except Exception as e:
                logger.error(f"{date_str} 早盘分析失败: {e}")
            await asyncio.sleep(2)

        # 生成晚盘报告
        if evening_news:
            try:
                report = await analyze_news(evening_news, date_str, "evening")
                if report:
                    await save_report_to_db(report)
            except Exception as e:
                logger.error(f"{date_str} 晚盘分析失败: {e}")
            await asyncio.sleep(2)

    logger.info("回溯完成!")


if __name__ == "__main__":
    asyncio.run(main())
