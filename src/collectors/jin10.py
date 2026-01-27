"""金十数据 Playwright 采集器"""

import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from loguru import logger

from src.models import NewsItem, SourceType
from .playwright_base import PlaywrightCollector


class Jin10Collector(PlaywrightCollector):
    """金十数据快讯采集器"""

    async def get_urls(self) -> list[str]:
        return ["https://www.jin10.com/"]

    async def parse_page(self, url: str, content: str) -> list[NewsItem]:
        soup = BeautifulSoup(content, "html.parser")
        items = []
        beijing_tz = timezone(timedelta(hours=8))

        flash_items = soup.select(".jin-flash-item")
        for item in flash_items[:30]:
            try:
                time_el = item.select_one(".item-time")
                content_el = item.select_one(".right-content")

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
                    source="金十数据",
                    source_type=SourceType.INTERNATIONAL,
                    url=url,
                    published_at=pub_time,
                ))
            except Exception as e:
                logger.debug(f"解析金十条目失败: {e}")
                continue

        return items

    def _parse_time(self, time_text: str, tz) -> datetime:
        now = datetime.now(tz)
        match = re.search(r"(\d{1,2}):(\d{2}):(\d{2})", time_text)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return now.replace(hour=h, minute=m, second=s, microsecond=0)
        return now
