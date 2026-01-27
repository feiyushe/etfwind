"""东方财富快讯 Playwright 采集器"""

import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from loguru import logger

from src.models import NewsItem, SourceType
from .playwright_base import PlaywrightCollector


class EastMoneyPlaywrightCollector(PlaywrightCollector):
    """东方财富快讯采集器（Playwright 版本）"""

    async def get_urls(self) -> list[str]:
        return ["https://kuaixun.eastmoney.com/"]

    async def parse_page(self, url: str, content: str) -> list[NewsItem]:
        soup = BeautifulSoup(content, "html.parser")
        items = []

        news_links = soup.select(".news_detail_link")
        for link in news_links[:30]:
            try:
                text_el = link.select_one(".news_detail_text")
                title = text_el.get_text(strip=True) if text_el else ""

                if not title or len(title) < 10:
                    continue

                news_url = link.get("href", url)
                if news_url.startswith("//"):
                    news_url = "https:" + news_url

                items.append(NewsItem(
                    title=title,
                    content=title,
                    source="东财快讯",
                    source_type=SourceType.DOMESTIC,
                    url=news_url,
                    published_at=datetime.now(timezone(timedelta(hours=8))),
                ))
            except Exception as e:
                logger.debug(f"解析东财条目失败: {e}")
                continue

        return items
