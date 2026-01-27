"""测试 API 响应"""
import asyncio
import httpx
from src.config import settings
from src.web.database import init_db, get_today_news
from src.analyzers.prompts import SYSTEM_PROMPT, INVESTMENT_ANALYSIS_PROMPT


async def test_with_urls():
    await init_db()
    news = await get_today_news()

    # 模拟 _format_news 的逻辑，包含 URL
    news_lines = []
    for i, item in enumerate(news[:30], 1):
        source = item.get("source", "")
        title = item.get("title", "")
        url = item.get("url", "")
        if item.get("language") == "en" and item.get("summary_zh"):
            title = item.get("summary_zh")
        if url:
            news_lines.append(f"{i}. [{source}] {title} | {url}")
        else:
            news_lines.append(f"{i}. [{source}] {title}")

    news_content = "\n".join(news_lines)
    prompt = INVESTMENT_ANALYSIS_PROMPT.format(news_content=news_content)

    print(f"新闻数: {len(news[:30])}")
    print(f"Prompt长度: {len(prompt)} 字符")

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

        # 检查 JSON 是否完整
        if content.strip().endswith("```"):
            print("JSON 完整: 是")
        else:
            print("JSON 完整: 否")
            print(f"末尾100字符: {content[-100:]}")


if __name__ == "__main__":
    asyncio.run(test_with_urls())
