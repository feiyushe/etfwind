"""华尔街见闻 Playwright 采集器"""

import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from loguru import logger

from src.models import NewsItem, SourceType
from .playwright_base import PlaywrightCollector


class WallStreetCNCollector(PlaywrightCollector):
    """华尔街见闻快讯采集器"""

    async def get_urls(self) -> list[str]:
        return ["https://wallstreetcn.com/live/global"]

    async def parse_page(self, url: str, content: str) -> list[NewsItem]:
        soup = BeautifulSoup(content, "html.parser")
        items = []
        beijing_tz = timezone(timedelta(hours=8))

        live_items = soup.select(".live-item")
        for item in live_items[:30]:
            try:
                time_el = item.select_one(".live-item_created")
                content_el = item.select_one(".live-item_main")

                title = content_el.get_text(strip=True) if content_el else ""
                if not title or len(title) < 10:
                    continue

                pub_time = None
                if time_el:
                    time_text = time_el.get_text(strip=True)
                    pub_time = self._parse_time(time_text, beijing_tz)

                items.append(NewsItem(
                    title=title,
                    content=title,
                    source="华尔街见闻",
                    source_type=SourceType.INTERNATIONAL,
                    url=url,
                    published_at=pub_time,
                ))
            except Exception as e:
                logger.debug(f"解析华尔街见闻条目失败: {e}")
                continue

        return items

    def _parse_time(self, time_text: str, tz) -> datetime:
        now = datetime.now(tz)
        match = re.search(r"(\d{1,2}):(\d{2})", time_text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return now
