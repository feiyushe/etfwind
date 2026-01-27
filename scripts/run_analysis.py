"""运行增量分析"""
import asyncio
from src.analyzers import IncrementalAnalyzer
from src.web.database import init_db, get_today_news


async def main():
    await init_db()
    news = await get_today_news()
    print(f"新闻数: {len(news)}")

    analyzer = IncrementalAnalyzer()
    result = await analyzer.analyze_new_news(
        [n["id"] for n in news[:30]],
        force_full=True
    )

    print(f"market_narrative: {result.get('market_narrative', '')[:150]}")
    print(f"事件数: {len(result.get('focus_events', []))}")
    for e in result.get("focus_events", [])[:3]:
        print(f"  - {e.get('title')}")
        funds = e.get("related_funds", [])
        if funds:
            print(f"    ETF: {[f.get('code') for f in funds]}")


if __name__ == "__main__":
    asyncio.run(main())
