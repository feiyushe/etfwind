"""财联社新闻采集器"""

from datetime import datetime, timezone, timedelta
from typing import Any

from loguru import logger

from src.models import NewsItem, NewsCategory
from .base import BaseCollector


class CLSNewsCollector(BaseCollector):
    """财联社快讯采集器"""

    API_URL = "https://www.cls.cn/nodeapi/updateTelegraphList"

    async def collect(self) -> list[NewsItem]:
        """采集财联社快讯"""
        client = await self.get_client()

        params = {
            "app": "CailianpressWeb",
            "os": "web",
            "sv": "7.7.5",
            "rn": 50,
        }

        response = await client.get(self.API_URL, params=params)
        response.raise_for_status()

        data = response.json()
        items = []

        telegraphs = data.get("data", {}).get("roll_data", [])
        for item in telegraphs:
            news = self._parse_item(item)
            if news:
                items.append(news)

        return items

    def _parse_item(self, item: dict[str, Any]) -> NewsItem | None:
        """解析单条快讯"""
        try:
            title = item.get("title") or item.get("content", "")[:50]
            content = item.get("content", "")

            if not title and not content:
                return None

            # 解析时间
            ctime = item.get("ctime")
            published_at = None
            if ctime:
                published_at = datetime.fromtimestamp(ctime, tz=timezone(timedelta(hours=8)))

            # 分类
            category = self._classify(title + content)

            return NewsItem(
                title=title[:100] if title else content[:100],
                content=content,
                source="财联社",
                published_at=published_at,
                category=category,
            )
        except Exception as e:
            logger.debug(f"解析财联社快讯失败: {e}")
            return None

    def _classify(self, text: str) -> NewsCategory:
        """简单分类"""
        if any(k in text for k in ["央行", "政策", "国务院", "发改委", "财政"]):
            return NewsCategory.MACRO
        if any(k in text for k in ["美股", "美联储", "欧洲", "日本", "外资"]):
            return NewsCategory.INTERNATIONAL
        if any(k in text for k in ["板块", "行业", "概念", "涨停", "跌停"]):
            return NewsCategory.INDUSTRY
        if any(k in text for k in ["公司", "股份", "集团", "业绩", "财报"]):
            return NewsCategory.COMPANY
        return NewsCategory.OTHER
