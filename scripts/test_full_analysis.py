"""测试完整分析流程"""
import asyncio
import httpx
from src.config import settings
from src.web.database import init_db, get_today_news, get_news_by_ids
from src.analyzers.prompts import SYSTEM_PROMPT, INVESTMENT_ANALYSIS_PROMPT


async def test_full_analysis():
    await init_db()
    news = await get_today_news()
    ids = [n["id"] for n in news[:30]]

    # 使用 get_news_by_ids 获取新闻（与 IncrementalAnalyzer 相同）
    news_list = await get_news_by_ids(ids)
    print(f"获取新闻: {len(news_list)} 条")

    # 格式化新闻（与 _format_news 相同）
    lines = []
    for i, item in enumerate(news_list[:30], 1):
        source = item.get("source", "")
        title = item.get("title", "")
        url = item.get("url", "")
        if item.get("language") == "en" and item.get("summary_zh"):
            title = item.get("summary_zh")
        if url:
            lines.append(f"{i}. [{source}] {title} | {url}")
        else:
            lines.append(f"{i}. [{source}] {title}")

    news_content = "\n".join(lines)
    prompt = INVESTMENT_ANALYSIS_PROMPT.format(news_content=news_content)

    print(f"Prompt 长度: {len(prompt)} 字符")

    # 调用 API
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{settings.claude_base_url.rstrip('/')}/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": settings.claude_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": settings.claude_model,
                "max_tokens": 16384,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        data = response.json()

        print(f"stop_reason: {data.get('stop_reason')}")
        print(f"usage: {data.get('usage')}")

        content = data["content"][0]["text"] if data.get("content") else ""
        print(f"输出长度: {len(content)} 字符")

        # 检查完整性
        if "```" in content:
            if content.strip().endswith("```"):
                print("JSON 完整: 是")
            else:
                print("JSON 完整: 否 - 未以 ``` 结尾")
                print(f"末尾: {content[-150:]}")
        else:
            print("无 markdown 代码块")


if __name__ == "__main__":
    asyncio.run(test_full_analysis())
